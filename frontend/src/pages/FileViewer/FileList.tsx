import { Box } from "@mui/material";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { FixedSizeGrid as Grid } from "react-window";
import { FileMetadataDTO } from "../../api";
import { FileView, MenuOption } from "../../components/FileView";
import "../../index.css";
import { useOpenFileMutation } from "../../utils/mutations";

type FileListItem = {
  file: FileMetadataDTO;
  caption?: string;
};

export type Scroller = {
  scrollToTop: () => void;
};

type Variant = "small" | "medium" | "large";

type Props = {
  variant?: Variant;
  totalItems: number;
  itemProvider: (idx: number) => FileListItem | undefined;
  openOnDoubleClick?: boolean;
  scrollerRef: React.MutableRefObject<Scroller | null>;
  menuOptions: MenuOption[];
  showCaptions?: boolean;
};

export const FileList = ({
  totalItems,
  itemProvider,
  variant = "medium",
  openOnDoubleClick = true,
  scrollerRef,
  menuOptions,
  showCaptions = false,
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
    };
  }, [scrollerRef]);

  return (
    <div ref={containerRef}>
      <Grid
        ref={gridRef}
        columnCount={numColumns + 2}
        rowCount={numRows}
        columnWidth={elementSize + spacing}
        rowHeight={elementSize + spacing + (showCaptions ? 50 : 0)}
        height={height}
        width={realWidth + 2 * (elementSize + spacing) + 16}
        className="customScrollBar"
        // onItemsRendered={(x) => {
        //   console.log(
        //     `rendering: ${x.visibleRowStartIndex} - ${x.visibleRowStopIndex}, loading: ${x.overscanRowStartIndex} - ${x.overscanRowStopIndex}`
        //   );
        // }}
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
    </div>
  );
};
