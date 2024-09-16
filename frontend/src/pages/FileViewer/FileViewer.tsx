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

type FileWithScoresMaybe = FileMetadataDTO & {
  denseScore?: number;
  totalScore?: number;
  lexicalScore?: number;
};

type Props = {
  onNavigateToDescription: (fileId: number) => void;
};

export const FileViewer = ({ onNavigateToDescription }: Props) => {
  const [dataSource, setDataSource] = useState<DataSource>("all");
  const [embeddingSimilarityItems, setEmbeddingSimilarityItems] = useState<
    FileWithScoresMaybe[]
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
          data: x.results.map((item) => ({
            ...item.file,
            denseScore: item.denseScore,
            lexicalScore: item.lexicalScore,
            totalScore: item.totalScore,
          })),
          offset: x.offset,
          total: x.total,
        }));
    },
    [searchQuery]
  );

  useEffect(() => {
    setDataSource(searchQuery === "" ? "all" : "search");
  }, [searchQuery]);

  const { loaded, numTotalItems, getItem } =
    usePaginatedQuery<FileWithScoresMaybe>(
      FETCH_LIMIT,
      dataSource === "all" ? allFilesProvider : searchedFilesProvider
    );

  const scrollerRef = useRef<Scroller | null>(null);

  const findItemsWithSimilarDescriptionMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().loadApi.findItemsWithSimilarDescriptionsLoadFindWithSimilarDescriptionPost(
        {
          findSimilarItemsRequest: { fileId },
        }
      ),
    onSuccess: (data) => {
      setEmbeddingSimilarityItems(data.map((x) => x.file));
      setDataSource("embedding-similarity");
      scrollerRef.current?.scrollToTop();
    },
  });

  const findVisuallySimilarItemsMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().loadApi.findVisuallySimilarImagesLoadFindVisuallySimilarPost({
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
            showCaptions={true}
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
              let caption = "";
              const nf = (x: number | undefined) =>
                x == null ? "none" : `${Math.round(x * 100) / 100}`;
              if (file.totalScore != null) {
                caption += `s: ${nf(file.totalScore)} `;
                caption += `l: ${nf(file.lexicalScore)} `;
                caption += `d: ${nf(file.denseScore)} `;
              }
              caption += file.description;
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
            menuOptions={[
              {
                caption: "show description",
                handler: (f) => onNavigateToDescription(f.id),
              },
              {
                caption: "find semantically similar items",
                handler: (f) =>
                  findItemsWithSimilarDescriptionMutation.mutate(f.id),
              },
              {
                caption: "find visually similar items",
                handler: (f) => findVisuallySimilarItemsMutation.mutate(f.id),
              },
            ]}
          />
        ) : (
          <div>loading</div>
        )}
      </Box>
    </Box>
  );
};
