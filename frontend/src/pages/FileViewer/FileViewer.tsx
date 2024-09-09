import { Box } from "@mui/material";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { FixedSizeGrid as Grid } from "react-window";
import { FileMetadataDTO } from "../../api";
import { getApis } from "../../api/initializeApis";
import { FileView } from "../../components/FileView";
import "../../index.css";
import { SearchBar } from "./SearchBar";

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
      setFilesToShow(data);
    },
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
