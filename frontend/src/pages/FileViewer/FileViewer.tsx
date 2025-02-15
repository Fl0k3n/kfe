import AddIcon from "@mui/icons-material/Add";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import RemoveIcon from "@mui/icons-material/Remove";
import { Box, CircularProgress } from "@mui/material";
import {
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { FileType, SearchResultDTO } from "../../api";
import { getApis } from "../../api/initializeApis";
import {
  DataSource,
  FileWithScoresMaybe,
  Scroller,
} from "../../utils/commonTypes";
import { SEARCH_FETCH_LIMIT } from "../../utils/constants";
import { SelectedDirectoryContext } from "../../utils/directoryctx";
import {
  HistoryStack,
  QueryBasedSearchRequest,
  SemanticSearchRequest,
} from "../../utils/history";
import { getBase64ImageFromClipboard } from "../../utils/image";
import { useSemanticSearchMutations } from "../../utils/mutations";
import {
  getFileListVariant,
  higherFileListVariant,
  lowerFileListVariant,
  updateFileListVariant,
} from "../../utils/preferences";
import {
  useAllFilesProvider,
  usePaginatedQuery,
  useSearchedFilesProvider,
} from "../../utils/queries";
import { FileList } from "./FileList";
import { SearchBar } from "./SearchBar";

type Props = {
  scrollToIdx?: number;
  initialSearchQuery?: string;
  initialDataSource?: DataSource;
  initialEmbeddingSimilarityItems?: FileWithScoresMaybe[];
  historyStack: HistoryStack;
  onNavigateToDescription: (
    fileId: number,
    idx: number,
    searchQuery: string,
    dataSource: DataSource,
    embeddingSimilarityItems: FileWithScoresMaybe[]
  ) => void;
};

export const FileViewer = ({
  scrollToIdx,
  initialSearchQuery,
  initialDataSource,
  initialEmbeddingSimilarityItems,
  historyStack,
  onNavigateToDescription,
}: Props) => {
  const directory = useContext(SelectedDirectoryContext) ?? "";
  const [dataSource, setDataSource] = useState<DataSource>(
    initialDataSource ?? "all"
  );
  const [embeddingSimilarityItems, setEmbeddingSimilarityItems] = useState<
    FileWithScoresMaybe[]
  >(initialEmbeddingSimilarityItems ?? []);
  const [searchBarInitialQuery, setSearchBarInitialQuery] =
    useState(initialSearchQuery);
  const [searchQuery, setSearchQuery] = useState(initialSearchQuery ?? "");
  const [fileListVariant, setFileListVariant] = useState(
    getFileListVariant("large")
  );

  useEffect(() => {
    updateFileListVariant(fileListVariant);
  }, [fileListVariant]);

  useEffect(() => {
    setSearchQuery(initialSearchQuery ?? "");
    setDataSource(initialDataSource ?? "all");
  }, [directory, initialDataSource, initialSearchQuery]);

  const allFilesProvider = useAllFilesProvider(directory, SEARCH_FETCH_LIMIT);
  const searchedFilesProvider = useSearchedFilesProvider(
    directory,
    searchQuery,
    SEARCH_FETCH_LIMIT
  );

  const { loaded, numTotalItems, getItem } =
    usePaginatedQuery<FileWithScoresMaybe>(
      SEARCH_FETCH_LIMIT,
      dataSource === "all"
        ? allFilesProvider
        : dataSource === "search"
        ? searchedFilesProvider
        : undefined
    );

  const scrollerRef = useRef<Scroller | null>(null);
  const blockAutoScrollingToItemRef = useRef<boolean>(false);

  useLayoutEffect(() => {
    if (
      scrollToIdx == null ||
      scrollToIdx === 0 ||
      scrollerRef.current == null ||
      blockAutoScrollingToItemRef.current
    )
      return;
    scrollerRef.current.scrollToIdx(scrollToIdx);
    if (loaded) {
      // prevent scrolling when we returned from
      // metadata editor and entered a new query
      blockAutoScrollingToItemRef.current = true;
    }
  }, [loaded, scrollerRef, scrollToIdx]);

  const switchToEmbeddingSimilarityItems = (
    request: SemanticSearchRequest,
    data: SearchResultDTO[]
  ) => {
    setEmbeddingSimilarityItems(data.map((x) => x.file));
    setDataSource("embedding-similarity");
    historyStack.pushSemantic(request);
    scrollerRef.current?.scrollToTop();
  };

  const {
    findItemsWithSimilarDescriptionMutation,
    findItemsWithSimilarLLMDescriptionMutation,
    findSemanticallySimilarItemsMutation,
    findVisuallySimilarImagesMutation,
    findVisuallySimilarVideosMutation,
    findImagesSimilarToPastedImageMutation,
    runSemanticSearch,
  } = useSemanticSearchMutations(directory, switchToEmbeddingSimilarityItems);

  useEffect(() => {
    const pasteListener = (e: Event) => {
      getBase64ImageFromClipboard(e as ClipboardEvent).then((pastedImage) => {
        if (pastedImage) {
          findImagesSimilarToPastedImageMutation.mutate(pastedImage);
        }
      });
    };
    window.addEventListener("paste", pasteListener);
    return () => {
      window.removeEventListener("paste", pasteListener);
    };
  }, [findImagesSimilarToPastedImageMutation]);

  const goBackToPreviousSearch = useCallback(() => {
    if (historyStack.isEmpty()) return;
    historyStack.pop();
    let historyItem = historyStack.pop();
    if (historyItem == null || historyItem.isQuery) {
      const item =
        historyItem != null
          ? (historyItem.item as QueryBasedSearchRequest)
          : { query: "" };
      setSearchBarInitialQuery(item.query);
      setDataSource(item.query === "" ? "all" : "search");
      setSearchQuery(
        item.query === searchQuery ? item.query + " " : item.query
      );
      if (historyItem != null) {
        historyStack.pushQuery(item);
      }
    } else {
      runSemanticSearch(historyItem.item as SemanticSearchRequest);
    }
  }, [historyStack, runSemanticSearch, searchQuery]);

  useEffect(() => {
    const goBackHandler = (event: MouseEvent) => {
      if (event.button === 3) goBackToPreviousSearch();
    };
    window.addEventListener("mousedown", goBackHandler);
    return () => {
      window.removeEventListener("mousedown", goBackHandler);
    };
  }, [goBackToPreviousSearch]);

  return (
    <Box>
      <Box
        sx={{ pt: 4, display: "flex", width: "100%", justifyContent: "center" }}
      >
        <Box sx={{ width: "40%", pr: "8px" }}>
          <SearchBar
            key={searchBarInitialQuery}
            initialQuery={searchBarInitialQuery ?? ""}
            onSearch={(query) => {
              // ensure refresh
              setSearchQuery(query === searchQuery ? query + " " : query);
              setDataSource(query === "" ? "all" : "search");
              historyStack.pushQuery({ query });
            }}
            onEmptyEnter={() => {
              if (dataSource !== "all") {
                setDataSource("all");
                historyStack.pushQuery({ query: "" });
              }
            }}
          />
        </Box>
      </Box>
      <Box
        sx={{ mt: 3, display: "flex", width: "100%", justifyContent: "center" }}
      >
        {loaded || dataSource === "embedding-similarity" ? (
          <Box>
            <FileList
              showCaptions={false}
              scrollerRef={scrollerRef}
              variant={fileListVariant}
              itemProvider={(idx) => {
                const file =
                  dataSource === "embedding-similarity"
                    ? embeddingSimilarityItems[idx]
                    : getItem(idx);
                if (!file) {
                  return undefined;
                }
                let caption = "";
                const nf = (x: number | undefined) =>
                  x == null ? "none" : `${Math.round(x * 100) / 100}`;
                if (file.totalScore != null) {
                  caption += `s: ${nf(file.totalScore)} `;
                  caption += `l: ${nf(file.lexicalScore)} `;
                  caption += `d: ${nf(file.denseScore)} `;
                }
                // caption += file.description;
                return {
                  file,
                  caption,
                };
              }}
              totalItems={
                dataSource === "embedding-similarity"
                  ? embeddingSimilarityItems.length
                  : numTotalItems
              }
              resultsFiltered={dataSource === "search"}
              menuOptions={[
                {
                  caption: "show in native explorer",
                  handler: (f) => {
                    getApis().accessApi.openInNativeExplorerAccessOpenInDirectoryPost(
                      {
                        openFileRequest: { fileId: f.id },
                        xDirectory: directory,
                      }
                    );
                    navigator.clipboard.writeText(f.name);
                  },
                },
                {
                  caption: "show metadata",
                  handler: (f, idx) =>
                    onNavigateToDescription(
                      f.id,
                      idx,
                      searchQuery,
                      dataSource,
                      embeddingSimilarityItems
                    ),
                },
                {
                  caption: "copy file name",
                  handler: (f) => {
                    navigator.clipboard.writeText(f.name);
                  },
                },
                {
                  caption: "find items with similar description",
                  handler: (f) => {
                    findItemsWithSimilarDescriptionMutation.mutate(f.id);
                  },
                  hidden: (f) => f.description === "",
                },
                {
                  caption: "find items with similar metadata",
                  handler: (f) => {
                    findSemanticallySimilarItemsMutation.mutate(f.id);
                  },
                  hidden: (f) =>
                    f.description === "" &&
                    (f.ocrText == null || f.ocrText === "") &&
                    (f.transcript == null || f.transcript === ""),
                },
                {
                  caption: "find items with similar LLM description",
                  handler: (f) => {
                    findItemsWithSimilarLLMDescriptionMutation.mutate(f.id);
                  },
                  hidden: (f) =>
                    f.llmDescription == null || f.llmDescription === "",
                },
                {
                  caption: "find similar images",
                  handler: (f) => {
                    findVisuallySimilarImagesMutation.mutate(f.id);
                  },
                  hidden: (f) => f.fileType !== FileType.Image,
                },
                {
                  caption: "find similar videos",
                  handler: (f) => {
                    findVisuallySimilarVideosMutation.mutate(f.id);
                  },
                  hidden: (f) => f.fileType !== FileType.Image,
                },
              ]}
            />
            <Box>
              <RemoveIcon
                className={`menuIcon${
                  fileListVariant === "small" ? " menuIconDisabled" : ""
                }`}
                onClick={() => {
                  setFileListVariant(lowerFileListVariant(fileListVariant));
                }}
                sx={{
                  position: "fixed",
                  bottom: "80px",
                  left: "20px",
                }}
              ></RemoveIcon>
              <AddIcon
                className={`menuIcon${
                  fileListVariant === "large" ? " menuIconDisabled" : ""
                }`}
                onClick={() => {
                  setFileListVariant(higherFileListVariant(fileListVariant));
                }}
                sx={{
                  position: "fixed",
                  bottom: "130px",
                  left: "20px",
                }}
              ></AddIcon>
              {!historyStack.isEmpty() && (
                <ArrowBackIcon
                  className={"menuIcon"}
                  onClick={goBackToPreviousSearch}
                  sx={{
                    position: "fixed",
                    bottom: "180px",
                    left: "20px",
                  }}
                ></ArrowBackIcon>
              )}
            </Box>
          </Box>
        ) : (
          <Box>
            <CircularProgress
              sx={{ minWidth: "80px", minHeight: "80px", mt: 5 }}
            />
          </Box>
        )}
      </Box>
    </Box>
  );
};
