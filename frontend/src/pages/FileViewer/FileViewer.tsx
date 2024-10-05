import { Box, CircularProgress } from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { FileMetadataDTO, SearchResultDTO } from "../../api";
import { getApis } from "../../api/initializeApis";
import { getBase64ImageFromClipboard } from "../../utils/image";
import { usePaginatedQuery } from "../../utils/mutations";
import { FileList, Scroller } from "./FileList";
import { SearchBar } from "./SearchBar";

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

  const switchToEmbeddingSimilarityItems = (data: SearchResultDTO[]) => {
    setEmbeddingSimilarityItems(data.map((x) => x.file));
    setDataSource("embedding-similarity");
    scrollerRef.current?.scrollToTop();
  };

  const findItemsWithSimilarDescriptionMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().loadApi.findItemsWithSimilarDescriptionsLoadFindWithSimilarDescriptionPost(
        {
          findSimilarItemsRequest: { fileId },
        }
      ),
    onSuccess: switchToEmbeddingSimilarityItems,
  });

  const findVisuallySimilarItemsMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().loadApi.findVisuallySimilarImagesLoadFindVisuallySimilarPost({
        findSimilarItemsRequest: { fileId },
      }),
    onSuccess: switchToEmbeddingSimilarityItems,
  });

  const findImagesSimilarToPastedImageMutation = useMutation({
    mutationFn: (imageDataBase64: string) =>
      getApis().loadApi.findVisuallySimilarImagesToUploadedImageLoadFindSimilarToUploadedImagePost(
        {
          findSimilarImagesToUploadedImageRequest: { imageDataBase64 },
        }
      ),
    onSuccess: switchToEmbeddingSimilarityItems,
  });

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
            showCaptions={false}
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
                caption: "show metadata",
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
