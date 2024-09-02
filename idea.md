frontend features:
- search bar:
    - input should be text
    - allow special stuff prefixed by @; e.g. "@author=naborzny naborzny sie wyjebal"
        - tags: author="who", type="audio/video/image/screenshot", 
    - autocomplete e.g. @au tab -> @author
    - when something is correctly found attach search query to result file (list of matched queries) and use that for better search
- main file area:
    - simple list, something like normal file explorer but web-based, results returned via http (file thumbnails, allow playing, opening)
    - by default sorted by date added (newest first)
    - on right click on a file:
        - find similar text based
        - for images - find similar embedding based
        - edit tags/description
- untagged files tab:
 - show files that were untagged, allow editing that
- file explorer rooted at the target folder (konrad)
- caching of files + thumbnails on frontend - this must be fast


backend features:
- audio to text; for videos and audio files - treat raw audio text as a feautre in addition to descirpption; maybe also keywords for better text-based search
- handle description, tags, raw audio as features that should be searchable
- backup copy for all metadata to single file and restoring state from that
- auto detect and process new files added to the directory
- http server able to serve files, thumbnails, accept changes, searching etc


---

- if quality is not good enough instead of using llama 3.1 for transcript correction generate a large structured prompt with multiple examples and manually pass it to gpt
- no need for faiss - even for 50k items similarity search takes 10s of ms
