# kfe

Cross-platform File Explorer and Search Engine for Multimedia.

# Features
- Full privacy. Data never leaves your machine.
- Text query-based search that accounts for:
    - visual aspects of images and videos based on [CLIP](https://huggingface.co/docs/transformers/en/model_doc/clip) embeddings,
    - transcriptions that are automatically generated for audio and video files,
    - text that is automatically extracted from images,
    - descriptions that you can manually write using GUI.
- Similarity search capabilities:
    - find images or videos similar to one of images from your directory,
    - find images similar to any image pasted from the clipboard,
    - find files with semantically similar metadata (descriptions, transcriptions or text extracted from image).
- Browser GUI that lets you easily use all of those search options, browse files and edit file metadata.
- Standalone program that depends only on ffmpeg. Project includes all the necessary database and search features.
- Works offline, can work with and without GPU.
- Works on Mac, Linux and Windows.
- Supports English and Polish languages.

## Intended use cases

The application was designed for directories containing up to 10k images, short (<5 minutes) videos, or audio files. File names are assumed to be non-descriptive. Examples of such directories are:
- phone gallery or audio recordings copied to PC,
- data dumps from messaging apps like Messenger (Messenger built-in search works only for text messages, but they allow downloading all media, which can be searched using this app),
- saved memes.

# YouTube Demo


<div align="center">
    <a href="https://www.youtube.com/watch?v=LSe0QB6dzEY">
        <img src="https://img.youtube.com/vi/LSe0QB6dzEY/0.jpg" alt="Project Demo" />
    </a>
    <p><a href="https://www.youtube.com/watch?v=LSe0QB6dzEY">Watch the demo on YouTube</a></p>

</div>

# Installation

1. Make sure that you have `python>=3.10` and `ffmpeg` with `ffprobe` installed:
- For ffmpeg installation, see: https://ffmpeg.org/download.html.
- To verify installation run command line and type `ffmpeg -version` and `ffprobe -version`, both should print some results.

2. Optional: create virtual environment:
 - Mac/Linux:
```sh
python -m venv env
source ./env/bin/activate
```
- Windows:
```sh
python -m venv env
env\Scripts\activate
```

3. Install the project:

```sh
pip install kfe
```

# Running

1. In console run:
```sh
kfe
```

If you get an error that the default `8000` port is taken, you can change it using `kfe --port <other port>`. For more options run `kfe --help`.

2. Open `http://localhost:8000` in the browser.

3. Follow instructions on GUI, analyzing directory can take some time, but later searches will be fast. All analysis information will be stored on your disk and won't need to be done again. Adding first directory might be especially slow since all AI models will be downloaded. After they are downloaded application will work offline.

If you see CUDA out of memory errors you can still run the application using CPU with `kfe --cpu`. The transcription model is the most resource demanding, see the next section for instruction how to change it.

If you are on Linux and want to run application on system startup you can clone the project and run `./systemd/install_with_systemd.sh`.

# Models

Application uses the following models/libraries for english directories:
- Transcriptions - for each audio and video files transcription is generated using [openai/whisper-large-v3](https://huggingface.co/openai/whisper-large-v3) model if you have CUDA or Apple silicon, otherwise [openai/whisper-base](https://huggingface.co/openai/whisper-base). This model requires more hardware resources than other models, you might want to change it, see the next section.
- OCR - for each image application attempts to extract text using [easyocr](https://github.com/JaidedAI/EasyOCR) library.
- CLIP embeddings - for each image and video (from which multiple image frames are extracted) application generates CLIP embeddings using [openai/clip](https://huggingface.co/openai/clip-vit-base-patch32) model. This enables searching images by arbitrary text, without need for any annotations.
- Text embeddings - application generates embeddings of each type of text that can be searched (descriptions that you can write manually, transcriptions and OCR results) using [BAAI/bge-large-en-v1.5](https://huggingface.co/BAAI/bge-large-en-v1.5) model.
- Text lemmatization - each type of text and every user query is preprocessed using [spacy/en_core_web_trf](https://spacy.io/models/en#en_core_web_lg) lemmatization model for lexical search purposes. If you are unfamilar what this means, the tldr is that different forms of the same word (like `work = working = worked`) will be treated the same in this type of search.

## Changing models

Application uses models from huggingface, for various reasons you might want to change them. Transcription model is the most resource-demanding and can be changed with: `kfe --transcription-model <huggingface model id>`, where model id could be, for example, `openai/whisper-small`. See `kfe --help` for more info.

Currently other models can be changed only by modifying the source code. To do that, see [backend/kfe/dependencies.py](backend/kfe/dependencies.py) file and adjust it accordingly. If you change embedding model make sure to remove `.embeddings` directory so that embeddings will be recreated.

You might also want to use paid models or models hosted in the cloud, such as OpenAI Whisper through the API. There is no support (and no plans) for that, you would need to reimplement transcriber interface in [backend/kfe/features/transcriber.py](backend/kfe/features/transcriber.py) to achieve it.


# How does the application work?

Application allows you to search individual directories. You can use multiple directories, but no information is shared between them, and you cannot search all of them at once. When you register a directory using GUI the following things happen.

### Initialization

1. Application creates a sqlite database file in the directory, named `.kfe.db`. This database stores almost all the metadata about files in the selected directory, including descriptions, extracted transcriptions, lemmatization results and more. You can see the SQL table format in [backend/kfe/persistence/model.py](backend/kfe/persistence/model.py). 
2. Applications scans the directory and adds every multimedia file to the database, subdirectories and other types of files are ignored.
3. For each file, application extracts relevant text (OCR for images, transcriptions for videos and audio) and lemmatizes it. Results are written to the database so it can be done only once.
4. Application generates various types of embeddings and stores them in `.embeddings` directory, there is a file with encoded embeddings for each original file in the directory. See `models` above to have an idea what embeddings are generated.
5. Application loads the data to various search structures:
    - original and lemmatized text is split into words and added to a reverse index structure, which is a map of `word -> list of files in which the word appears`,
    - embeddings are loaded into numpy matrices (different matrices for different types of embeddings).
6. Application generates thumbnails and saves them in `.thumbnails` subdirectory of the selected folder.
7. Application begins to watch for directory changes, processing new files the same way as above and cleaning up after the removed ones. Note that the GUI does NOT allow you to modify any files (nor does the application do so by itself), you must use your native file explorer for that.

If you restart the application and directory was already initialized before then only steps 5-7 happen.

### Query-time

At this stage directory is marked as ready for querying. When you enter a query without any `@` modifiers the following things happen.

1. Lexical/keyword search:
    - query is lemmatized and split into words,
    - reverse index is queried to load files which have descriptions, OCRs or transcriptions that contain some of the words from the query,
    - files are scored according to [BM25 metric](https://en.wikipedia.org/wiki/Okapi_BM25).
2. Semantic search:
    - application generates query embedding using text embedding model,
    - matrices with pre-computed embeddings of descriptions, OCRs and transcriptions are used to compute cosine similarity of the query embedding and all of those embeddings.
3. CLIP search:
    - application generates query embedding using text CLIP encoder,
    - matrices with pre-computed clip embeddings of images and videos are used to compute cosine similarity of the query embedding and all of those embeddings.
4. Ordering results using hybrid approach. A variation of [reciprocal rank fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) is used to combine results for all of those search modes. The variation is a custom problem-specific metric that attempts to weight confidence of individual retrievers and not just the ranks. See [backend/kfe/utils/search.py](backend/kfe/utils/search.py) for more details.
5. Ordered results with file thumbnails are returned to the UI which presents them to the user.


All of those structures and algorithms are written from scratch and included in the project. The application doesn't use tools such as elastic search for lexical search or faiss for similarity search. The assumption is that directories are not massive, they can contain up to few tens of thousands of files, not hundreds of thousands of files. For such use case this approach should work seamlessly on consumer grade machines (~200ms of search latency for a PC with 12gen i5 for a directory with ~5000 files with latency dominated by generation of embeddings and not search).

Application lets you also choose search mode (e.g., search only transcriptions) and filter results, GUI help in the top right corner enumerates all the options.


### Resource usage

Application loads models in a lazy manner (only when they are needed) and recycles them automatically. If you have application running in the background it doesn't consume any GPU memory. When models required for querying are loaded they use about 2GB of memory.

For initialization, a heavier transcription model will be loaded if there are audio files. During directory initialization application can consume up to 5GB of GPU memory. It can work on CPU the same but will likely be slower, you can pass `--cpu` flag to force CPU usage.

Apart from that, application requires ~1GB of RAM when idle and >2GB when used (exact numbers depend on how many files you have, 2GB was for ~10k files). Add GPU stats to that if you are not using GPU.

Storage: All models and dependencies require <10GB of disk space.


### Removing all data created or downloaded by the application

Models are stored in `.kfe` directory in the home folder, OCR model is stored in `.EasyOCR` directory in home folder. Apart from that in each registered directory there are `.embeddings` and `.thumbnails` folders and `.kfe.db` file.

To backup generated or manually written metadata it suffices to copy `.kfe.db` file.


# Programmatic access to the data and API

Metadata is stored in sqlite database, you can access it using any sqlite library or tool. For example using `sqlite3` tool on Linux:

```sh
sqlite3 .kfe.db
SELECT * FROM files;
```

Alternatively, if you want to reuse some of the utilities from this project:

```py
from pathlib import Path
from kfe.persistence.db import Database
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.persistence.model import FileMetadata

root_dir = Path('/todo') # directory where you have .kfe.db
files_db = Database(root_dir, log_sql=False)
await files_db.init_db()

async with files_db.session() as session:
    repo = FileMetadataRepository(session)
    files = await repo.load_all_files()
    for f in files:
        print(f'{f.name}: {f.transcript}')
```

To decode generated embeddings of a file:

```py
from pathlib import Path
from kfe.persistence.embeddings import EmbeddingPersistor

root_dir = Path('/todo') # directory where you have .kfe.db
file_name = 'todo.mp4' # file name inside this directory

embedding_persistor = EmbeddingPersistor(root_dir)
embeddings = embedding_persistor.load_without_consistency_check(file_name)

print(embeddings.__dict__.keys()) # ['description', 'ocr_text', 'transcription_text', 'clip_image', 'clip_video']
print(embeddings.transcription_text.embedding.shape) # (1024, )
```

To see all endpoints open http://localhost:8000/docs. To perform a search you can, for example, run:

```sh
curl -X POST "http://localhost:8000/load/search?offset=0&limit=10" \
     -H "X-Directory: NAME-OF-YOUR-DIRECTORY" \
     -H "Content-Type: application/json" \
     -d '{"query": "YOUR QUERY"}'

```