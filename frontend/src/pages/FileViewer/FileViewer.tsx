import { Box } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { FixedSizeGrid as Grid } from "react-window";
import { getApis } from "../../api/initializeApis";
import { FileView } from "../../components/FileView";
import "../../index.css";
import { SearchBar } from "./SearchBar";

export const FileViewer = () => {
  const filesQuery = useQuery({
    queryKey: ["idk"],
    queryFn: () => getApis().loadApi.getDirectoryFilesLoadGet(),
  });

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
          <SearchBar onSearch={() => null} />
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
              rowIndex * numColumns + columnIndex - 1 <
                filesQuery.data.length ? (
                <FileView
                  showName={false}
                  file={
                    filesQuery.data[rowIndex * numColumns + columnIndex - 1]
                  }
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
