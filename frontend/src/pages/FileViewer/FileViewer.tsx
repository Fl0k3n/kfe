import { Box } from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { FileMetadataDTO } from "../../api";
import { getApis } from "../../api/initializeApis";
import { usePaginatedQuery } from "../../utils/mutations";
import { FileList, Scroller } from "./FileList";
import { SearchBar } from "./SearchBar";

// type SearchBy = "total" | "dense" | "lexical";

// const sortSearchResults = (
//   srs: SearchResultDTO[],
//   by: SearchBy = "total"
// ): SearchResultDTO[] => {
//   const res = [...srs];
//   let compare = (a: SearchResultDTO, b: SearchResultDTO) =>
//     b.totalScore - a.totalScore;
//   if (by === "dense") {
//     compare = (a, b) => b.denseScore - a.denseScore;
//   } else if (by === "lexical") {
//     compare = (a, b) => b.lexicalScore - a.lexicalScore;
//   }
//   res.sort(compare);
//   return res;
// };

const FETCH_LIMIT = 200;

type DataSource = "all" | "search" | "embedding-similarity";

export const FileViewer = () => {
  const [dataSource, setDataSource] = useState<DataSource>("all");
  const [embeddingSimilarityItems, setEmbeddingSimilarityItems] = useState<
    FileMetadataDTO[]
  >([]);
  const [searchQuery, setSearchQuery] = useState("");

  const allFilesProvider = useCallback((offset: number) => {
    return getApis()
      .loadApi.getDirectoryFilesLoadGet({ offset, limit: FETCH_LIMIT })
      .then((x) => ({
        data: x.files,
        offset: x.offset,
        total: x.total,
      }));
  }, []);

  const searchedFilesProvider = useCallback(
    (offset: number) => {
      return getApis()
        .loadApi.searchLoadSearchPost({
          offset,
          limit: FETCH_LIMIT,
          searchRequest: { query: searchQuery },
        })
        .then((x) => ({
          data: x.results.map((item) => item.file),
          offset: x.offset,
          total: x.total,
        }));
    },
    [searchQuery]
  );

  useEffect(() => {
    setDataSource(searchQuery === "" ? "all" : "search");
  }, [searchQuery]);

  const { loaded, numTotalItems, getItem } = usePaginatedQuery<FileMetadataDTO>(
    FETCH_LIMIT,
    dataSource === "all" ? allFilesProvider : searchedFilesProvider
  );

  const scrollerRef = useRef<Scroller | null>(null);

  const findSimilarItemsMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().loadApi.findSimilarItemsLoadFindSimilarPost({
        findSimilarItemsRequest: { fileId },
      }),
    onSuccess: (data) => {
      setEmbeddingSimilarityItems(data.map((x) => x.file));
      setDataSource("embedding-similarity");
      scrollerRef.current?.scrollToTop();
    },
  });

  return (
    <Box>
      <Box
        sx={{ pt: 4, display: "flex", width: "100%", justifyContent: "center" }}
      >
        <Box sx={{ width: "40%", pr: "8px" }}>
          <SearchBar
            onSearch={(query) => {
              setSearchQuery(query);
            }}
            onEmptyEnter={() => {
              setDataSource("all");
            }}
          />
        </Box>
      </Box>
      <Box
        sx={{ mt: 3, display: "flex", width: "100%", justifyContent: "center" }}
      >
        {loaded ? (
          <FileList
            scrollerRef={scrollerRef}
            variant="large"
            itemProvider={(idx) => {
              const file =
                dataSource === "embedding-similarity"
                  ? embeddingSimilarityItems[idx]
                  : getItem(idx);
              if (!file) {
                return undefined;
              }
              return {
                file,
              };
            }}
            totalItems={
              dataSource === "embedding-similarity"
                ? embeddingSimilarityItems.length
                : numTotalItems
            }
            onRightClick={(x) => findSimilarItemsMutation.mutate(x.id)}
          />
        ) : (
          <div>loading</div>
        )}
      </Box>
    </Box>
  );
};
