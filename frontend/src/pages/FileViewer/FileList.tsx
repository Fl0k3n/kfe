import { Box, Typography } from "@mui/material";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { FixedSizeGrid as Grid } from "react-window";
import { FileView, MenuOption } from "../../components/FileView";
import "../../index.css";
import { FileListItem, Scroller } from "../../utils/commonTypes";
import { useOpenFileMutation } from "../../utils/mutations";
import { FileListVariant } from "../../utils/preferences";

type Props = {
  variant?: FileListVariant;
  totalItems: number;
  itemProvider: (idx: number) => FileListItem | undefined;
  openOnDoubleClick?: boolean;
  scrollerRef: React.MutableRefObject<Scroller | null>;
  menuOptions: MenuOption[];
  showCaptions?: boolean;
  resultsFiltered: boolean;
};

export const FileList = ({
  totalItems,
  itemProvider,
  variant = "medium",
  openOnDoubleClick = true,
  scrollerRef,
  menuOptions,
  showCaptions = false,
  resultsFiltered,
}: Props) => {
  const realWidth = 1200;
  const elementSize =
    variant === "medium" ? 150 : variant === "large" ? 250 : 100;
  const spacing = 50;
  const bottomPadding = 50;
  const [innerHeight, setInnerHeight] = useState(window.innerHeight);
  const [height, setHeight] = useState(window.innerHeight / 2);

  const numColumns = Math.floor(
    (realWidth + spacing) / (elementSize + spacing)
  );
  const numRows = Math.ceil(totalItems / numColumns);

  const itemIdx = (rowIdx: number, colIdx: number) =>
    rowIdx * numColumns + colIdx - 1;

  const openFileMutation = useOpenFileMutation();

  const containerRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<Grid>(null);

  useEffect(() => {
    const handler = () => {
      setInnerHeight(window.innerHeight);
    };
    window.addEventListener("resize", handler);
    return () => {
      window.removeEventListener("resize", handler);
    };
  }, []);

  useLayoutEffect(() => {
    if (containerRef.current) {
      setHeight(
        innerHeight -
          containerRef.current.getBoundingClientRect().top -
          bottomPadding
      );
    }
  }, [innerHeight]);

  useLayoutEffect(() => {
    scrollerRef.current = {
      scrollToTop: () => {
        if (gridRef.current) {
          gridRef.current.scrollTo({ scrollTop: 0 });
        }
      },
      scrollToIdx: (idx) => {
        if (gridRef.current) {
          gridRef.current.scrollToItem({
            align: "center",
            columnIndex: 0,
            rowIndex: Math.floor(idx / numColumns),
          });
        }
      },
    };
  }, [scrollerRef, numColumns]);

  return (
    <div ref={containerRef}>
      {totalItems > 0 ? (
        <Grid
          ref={gridRef}
          columnCount={numColumns + 2}
          rowCount={numRows}
          columnWidth={elementSize + spacing}
          rowHeight={elementSize + spacing + (showCaptions ? 50 : 0)}
          height={height}
          width={realWidth + 2 * (elementSize + spacing) + 16}
          className="customScrollBar"
          overscanRowCount={20}
        >
          {({ columnIndex, rowIndex, style }) => {
            const idx = itemIdx(rowIndex, columnIndex);
            return (
              <div
                style={{
                  ...style,
                  padding: `${spacing / 2}px`,
                }}
              >
                {columnIndex > 0 &&
                columnIndex < numColumns + 1 &&
                itemIdx(rowIndex, columnIndex) < totalItems ? (
                  <Box>
                    <FileView
                      showName={false}
                      file={itemProvider(idx)?.file}
                      height={elementSize}
                      width={elementSize}
                      onDoubleClick={() => {
                        const item = itemProvider(idx);
                        if (openOnDoubleClick && item) {
                          openFileMutation(item.file);
                        }
                      }}
                      showMenu={menuOptions.length > 0}
                      menuOptions={menuOptions}
                      idxWithinView={idx}
                    />
                    {showCaptions && <Box>{itemProvider(idx)?.caption}</Box>}
                  </Box>
                ) : (
                  <div></div>
                )}
              </div>
            );
          }}
        </Grid>
      ) : (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            justifyItems: "center",
          }}
        >
          <Typography>
            {resultsFiltered
              ? 'No matches, you can try different search algorithm, see help in top right corner or type "@" to see suggestions'
              : "Directory is empty"}
          </Typography>
        </Box>
      )}
    </div>
  );
};
