import operator
import os
import shutil
import pickle
import queue
import threading
import logging
import uuid
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Sized, Tuple


from src.modules.document.typing import Document, Metadata
from src.modules.document.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def dependable_faiss_import(no_avx2: Optional[bool] = None) -> faiss:
    """
    Import faiss if available, otherwise raise error.
    If FAISS_NO_AVX2 environment variable is set, it will be considered
    to load FAISS with no AVX2 optimization.

    Args:
        no_avx2: Load FAISS strictly with no AVX2 optimization
        so that the vectorstore is portable and compatible with other devices.
    """
    if no_avx2 is None and "FAISS_NO_AVX2" in os.environ:
        no_avx2 = bool(os.getenv("FAISS_NO_AVX2"))

    try:
        if no_avx2:
            from faiss import swigfaiss as faiss
        else:
            import faiss
    except ImportError:
        raise ImportError(
            "Could not import faiss python package. "
            "Please install it with `pip install faiss-gpu` (for CUDA supported GPU) "
            "or `pip install faiss-cpu` (depending on Python version)."
        )
    return faiss


def _len_check_if_sized(x: Any, y: Any, x_name: str, y_name: str) -> None:
    if isinstance(x, Sized) and isinstance(y, Sized) and len(x) != len(y):
        raise ValueError(
            f"{x_name} and {y_name} expected to be equal length but "
            f"len({x_name})={len(x)} and len({y_name})={len(y)}"
        )
    return


class VectorStore:
    def __init__(self, folder_path: str, embedding_model_name: str, query_instruction: str, device="cpu"):
        """
        Initializes the VectorStore with the specified folder path for saving indices,
        the name of the embedding model, and the computing device.
        """
        self.device = device
        self.embedding = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
            device=self.device,
            query_instruction=query_instruction
        )

        self.folder_path = folder_path

        # Initialize a thread-safe queue for save tasks and a lock to ensure exclusive access.
        self.save_tasks = queue.Queue()
        self.save_thread = threading.Thread(target=self._save_worker)
        self.save_thread.daemon = True
        self.save_thread.start()

        # Initialize docstore and index to document ID mapping.
        self.docstore: Dict[str, Document] = {}
        self.index_to_docstore_id = {}
        self.gpu_resources = None
        self.index = self._load_or_create_index()

    def _save_worker(self):
        """
        Worker thread that processes save tasks from the queue. It runs indefinitely
        and processes each task by calling the _perform_save method.
        """
        while True:
            task = self.save_tasks.get()
            if task is None:  # Use None as a signal to stop the worker.
                break
            self._perform_save(task)
            self.save_tasks.task_done()

    def _perform_save(self, index_name: str):
        """
        Performs the actual save operation for the index and docstore.
        This method is called by the worker thread.
        If the index is on GPU, it transfers it to CPU before saving.
        Before saving, creates backups of existing data. If the save fails,
        restores from the backups.
        """
        logger.info(f"Performing save operation for {index_name}.")
        path = Path(self.folder_path)
        path.mkdir(exist_ok=True, parents=True)

        backup_faiss_path = path / f"{index_name}_backup.faiss"
        backup_pkl_path = path / f"{index_name}_backup.pkl"

        original_faiss_path = path / f"{index_name}.faiss"
        original_pkl_path = path / f"{index_name}.pkl"

        try:
            if original_faiss_path.exists():
                shutil.copyfile(original_faiss_path, backup_faiss_path)
            if original_pkl_path.exists():
                shutil.copyfile(original_pkl_path, backup_pkl_path)

            self.rebuild_index()

            index_to_save = self.index
            if self.device == "cuda":
                logger.info("Transferring index from GPU to CPU for saving.")
                index_to_save = faiss.index_gpu_to_cpu(self.index)

            faiss.write_index(index_to_save, str(original_faiss_path))
            with open(original_pkl_path, "wb") as f:
                pickle.dump((self.docstore, self.index_to_docstore_id), f)
        except Exception as e:
            logger.error(
                f"Save operation failed: {e}, attempting to restore from backup.")
            if backup_faiss_path.exists():
                shutil.copyfile(backup_faiss_path, original_faiss_path)
            if backup_pkl_path.exists():
                shutil.copyfile(backup_pkl_path, original_pkl_path)
            logger.info("Restored data from backup.")
            raise  # Re-raise the exception to indicate failure
        finally:
            if backup_faiss_path.exists():
                backup_faiss_path.unlink()
            if backup_pkl_path.exists():
                backup_pkl_path.unlink()

        logger.info(f"Save operation for {index_name} completed successfully.")

    def save_index(self, index_name: str = "index"):
        """
        Queues a save task for the specified index. If a save operation is already in progress,
        the task will wait in the queue until it's processed by the worker thread.
        """
        logger.info(f"Queueing save operation for {index_name}.")
        self.save_tasks.put(index_name)

    def _load_or_create_index(self, index_name: str = "index"):
        path = Path(self.folder_path)
        faiss = dependable_faiss_import()

        _faiss_index_path = str(
            path / "{index_name}.faiss".format(index_name=index_name))
        _index_path = str(
            path / "{index_name}.pkl".format(index_name=index_name))

        if os.path.exists(_faiss_index_path) and os.path.exists(_index_path):
            index_cpu = faiss.read_index(_faiss_index_path)

            # load docstore and index_to_docstore_id
            with open(_index_path, "rb") as f:
                self.docstore, self.index_to_docstore_id = pickle.load(f)
        else:
            d = self.embedding.model.get_sentence_embedding_dimension()
            index_cpu = faiss.IndexFlatL2(d)
            self.docstore = {}
            self.index_to_docstore_id = {}

        if self.device == "cuda":
            self.gpu_resources = faiss.StandardGpuResources()
            logger.info("Loaded index to GPU.")
            return faiss.index_cpu_to_gpu(self.gpu_resources, 0, index_cpu)
        else:
            return index_cpu

    def rebuild_index(self):
        """
        Rebuilds the FAISS index based on the current state of the docstore. This is useful if the
        embedding model has changed or if the index has become corrupted or out-of-sync with the docstore.
        """
        # Load the FAISS index in CPU mode, regardless of the current device setting, to ensure full compatibility
        faiss = dependable_faiss_import()
        d = self.embedding.model.get_sentence_embedding_dimension()
        new_index_cpu = faiss.IndexFlatL2(d)

        # Embed all documents anew using the current embedding model
        all_docs = list(self.docstore.values())
        all_ids = list(self.docstore.keys())
        embeddings = np.array(self.embedding._embed_texts(
            [doc.page_content for doc in all_docs]), dtype=np.float32)

        # Clear and rebuild the index
        new_index_cpu.add(embeddings)

        # Reset the index-to-docstore ID mapping
        self.index_to_docstore_id = {
            i: doc_id for i, doc_id in enumerate(all_ids)}

        # Depending on the device, load the index into the appropriate memory (GPU or CPU)
        if self.device == 'cuda':
            # Ensure the GPU resources are properly initialized
            if not self.gpu_resources:
                self.gpu_resources = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(
                self.gpu_resources, 0, new_index_cpu)
        else:
            self.index = new_index_cpu

        logger.info("Index has been successfully rebuilt and reloaded.")

    def remove_documents_by_id(
        self, target_id_list: Optional[List[str]]
    ) -> Tuple[int, int]:
        if target_id_list is None:
            self.docstore = {}
            self.index_to_docstore_id = {}
            n_removed = self.index.ntotal
            n_total = self.index.ntotal
            self.index.reset()
            return n_removed, n_total
        set_ids = set(target_id_list)
        if len(set_ids) != len(target_id_list):
            raise VectorStoreError(
                "Duplicate ids in the list of ids to remove.")
        index_ids = [
            i_id
            for i_id, d_id in self.index_to_docstore_id.items()
            if d_id in target_id_list
        ]
        n_removed = len(index_ids)
        n_total = self.index.ntotal

        if self.device == "cuda":
            index_cpu = faiss.index_gpu_to_cpu(self.index)
            index_cpu.remove_ids(np.array(index_ids, dtype=np.int64))
            self.index = faiss.index_cpu_to_gpu(
                self.gpu_resources, 0, index_cpu)
        else:
            self.index.remove_ids(np.array(index_ids, dtype=np.int64))

        for i_id, d_id in zip(index_ids, target_id_list):
            del self.docstore[d_id]
            del self.index_to_docstore_id[i_id]
        self.index_to_docstore_id = {
            i: d_id for i, d_id in enumerate(self.index_to_docstore_id.values())
        }
        return n_removed, n_total

    def delete_documents_by_ids(self, target_ids: List[int]) -> Tuple[int, int]:
        if target_ids is None or len(target_ids) < 1:
            raise ValueError("Parameter target_ids cannot be empty.")

        id_to_remove = []
        for _id, doc in self.docstore.items():
            to_remove = False
            if doc.metadata.get_ids() in target_ids:
                to_remove = True
            if to_remove:
                id_to_remove.append(_id)
        return self.remove_documents_by_id(id_to_remove)

    def add_documents(
        self,
        docs: List[Document],
        ids: Optional[List[str]] = None
    ) -> List[Document]:
        embeds = self.embedding._embed_texts(
            [doc.page_content for doc in docs]
        )

        embeds = np.asarray(embeds, dtype=np.float32)
        ids = ids or [str(uuid.uuid4()) for _ in docs]
        if self.device == "cuda":
            index_cpu = faiss.index_gpu_to_cpu(self.index)
            index_cpu.add(embeds)
            self.index = faiss.index_cpu_to_gpu(
                self.gpu_resources, 0, index_cpu)
        else:
            self.index.add(embeds)

        for id_, doc in zip(ids, docs):
            self.docstore[id_] = doc

        starting_len = len(self.index_to_docstore_id)
        index_to_id = {starting_len + j: id_ for j, id_ in enumerate(ids)}
        self.index_to_docstore_id.update(index_to_id)
        return docs

    def similarity_search_with_score_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        fetch_k: int = 20,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        vector = np.array([embedding], dtype=np.float32)
        scores, indices = self.index.search(
            vector, k if filter is None else fetch_k)
        docs = []
        for j, i in enumerate(indices[0]):
            if i == -1:
                # This happens when not enough docs are returned.
                continue
            _id = self.index_to_docstore_id[i]
            doc = self.docstore.get(_id)
            if not isinstance(doc, Document):
                raise VectorStoreError(
                    f"Could not find document for id {_id}, got {doc}")
            if filter is not None:
                filter = {
                    key: [value] if not isinstance(value, list) else value
                    for key, value in filter.items()
                }
                if all(doc.metadata.to_dict().get(key) in value for key, value in filter.items()):
                    docs.append((doc, scores[0][j]))
            else:
                docs.append((doc, scores[0][j]))

        score_threshold = kwargs.get("score_threshold")
        if score_threshold is not None:
            cmp = (operator.le)
            docs = [
                (doc, similarity)
                for doc, similarity in docs
                if cmp(similarity, score_threshold)
            ]
        return docs[:k]

    def search(
        self,
        query,
        k=5,
        filter: Optional[Metadata] = None,
        fetch_k: int = 20,
        **kwargs
    ) -> List[Document]:

        if filter is not None:
            powerset = kwargs.get("powerset", True)
            filter = filter.to_filter(powerset)

        score_threshold = kwargs.get("score_threshold")
        if score_threshold is not None:
            kwargs.update({"score_threshold": score_threshold + 0.12})

        embeddings = self.embedding._embed_texts([query])
        docs_and_scores = self.similarity_search_with_score_by_vector(
            embeddings[0],
            k,
            filter=filter,
            fetch_k=fetch_k,
            **kwargs,
        )

        vd_docs = [doc for doc, _ in docs_and_scores if doc.is_valid()]

        return vd_docs[:k]
