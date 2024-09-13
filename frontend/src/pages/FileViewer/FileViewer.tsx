import { Box } from "@mui/material";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { FixedSizeGrid as Grid } from "react-window";
import { FileMetadataDTO, SearchResultDTO } from "../../api";
import { getApis } from "../../api/initializeApis";
import { FileView } from "../../components/FileView";
import "../../index.css";
import { SearchBar } from "./SearchBar";

type SearchBy = "total" | "dense" | "lexical";

const sortSearchResults = (
  srs: SearchResultDTO[],
  by: SearchBy = "total"
): SearchResultDTO[] => {
  const res = [...srs];
  let compare = (a: SearchResultDTO, b: SearchResultDTO) =>
    b.totalScore - a.totalScore;
  if (by === "dense") {
    compare = (a, b) => b.denseScore - a.denseScore;
  } else if (by === "lexical") {
    compare = (a, b) => b.lexicalScore - a.lexicalScore;
  }
  res.sort(compare);
  return res;
};

export const FileViewer = () => {
  const [filesToShow, setFilesToShow] = useState<FileMetadataDTO[]>([]);
  const filesQuery = useQuery({
    queryKey: ["idk"],
    queryFn: () => getApis().loadApi.getDirectoryFilesLoadGet(),
  });

  const searchMutation = useMutation({
    mutationFn: (query: string) =>
      getApis().loadApi.searchLoadSearchPost({ searchRequest: { query } }),
    onSuccess: (data) => {
      setFilesToShow(sortSearchResults(data).map((x) => x.file));
    },
  });

  const findSimilarItemsMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().loadApi.findSimilarItemsLoadFindSimilarPost({
        findSimilarItemsRequest: { fileId },
      }),
    onSuccess: (data) => {
      setFilesToShow(sortSearchResults(data).map((x) => x.file));
    },
  });

  const openFileMutation = useMutation({
    mutationFn: (fileName: string) =>
      getApis().accessApi.openFileAccessOpenPost({
        openFileRequest: { fileName },
      }),
  });

  useEffect(() => {
    if (filesQuery.data) {
      setFilesToShow(filesQuery.data);
    }
  }, [filesQuery.data]);

  if (!filesQuery.data) {
    return <div>loading</div>;
  }

  const realWidth = 1200;
  const elementSize = 150;
  const spacing = 50;

  const numColumns = Math.floor(
    (realWidth + spacing) / (elementSize + spacing)
  );

  const numRows = Math.ceil(filesQuery.data.length / numColumns);

  return (
    <Box>
      <Box
        sx={{ pt: 4, display: "flex", width: "100%", justifyContent: "center" }}
      >
        <Box sx={{ width: "40%", pr: "8px" }}>
          <SearchBar onSearch={(query) => searchMutation.mutate(query)} />
        </Box>
      </Box>
      <Box
        sx={{ mt: 3, display: "flex", width: "100%", justifyContent: "center" }}
      >
        <Grid
          columnCount={numColumns + 2}
          rowCount={numRows}
          columnWidth={elementSize + spacing} // Width of each square div
          rowHeight={elementSize + spacing} // Height of each square div
          height={780} // Height of the scrollable area
          width={realWidth + 2 * (elementSize + spacing) + 16} // Width of the scrollable area
          className="customScrollBar"
        >
          {({ columnIndex, rowIndex, style }) => (
            <div
              style={{
                ...style,
                padding: `${spacing / 2}px`,
              }}
            >
              {columnIndex > 0 &&
              columnIndex < numColumns + 1 &&
              rowIndex * numColumns + columnIndex - 1 < filesToShow.length ? (
                <FileView
                  showName={false}
                  file={filesToShow[rowIndex * numColumns + columnIndex - 1]}
                  height={elementSize}
                  width={elementSize}
                  onDoubleClick={() => {
                    openFileMutation.mutate(
                      filesToShow[rowIndex * numColumns + columnIndex - 1].name
                    );
                  }}
                  onRightClick={() =>
                    findSimilarItemsMutation.mutate(
                      filesToShow[rowIndex * numColumns + columnIndex - 1].id
                    )
                  }
                />
              ) : (
                // <div
                //   style={{
                //     background: "red",
                //     display: "flex",
                //     justifyContent: "center",
                //     alignItems: "center",
                //     height: "100%",
                //   }}
                // >
                //   {`Item ${rowIndex}, ${columnIndex}`}
                // </div>
                <div></div>
              )}
            </div>
          )}
        </Grid>
      </Box>
    </Box>
  );
};
