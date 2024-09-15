import { Box, Button, Container, TextField } from "@mui/material";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { FixedSizeList } from "react-window";
import { FileMetadataDTO } from "../../api";
import { getApis } from "../../api/initializeApis";
import { FileView } from "../../components/FileView";
import "../../index.css";
import {
  useOpenFileMutation,
  usePaginatedQuery,
  usePaginatedQueryExtraData,
} from "../../utils/mutations";

const FETCH_LIMIT = 100;

type Props = {
  startFileId?: number;
};

export const MetadataEditor = ({ startFileId }: Props) => {
  const [innerHeight, setInnerHeight] = useState(window.innerHeight);
  const [itemToScrollIdx, setItemToScrollIdx] = useState(0);
  const openFileMutation = useOpenFileMutation();
  const listRef = useRef<FixedSizeList<any>>(null);
  const allFilesProvider = useCallback((offset: number) => {
    return getApis()
      .loadApi.getDirectoryFilesLoadGet({ offset, limit: FETCH_LIMIT })
      .then((x) => ({
        data: x.files,
        offset: x.offset,
        total: x.total,
      }));
  }, []);

  const { loaded, numTotalItems, getItem } = usePaginatedQuery<FileMetadataDTO>(
    FETCH_LIMIT,
    allFilesProvider
  );

  const { updateExtraData: setDirtyStatus, getExtraData: getDirtyStatus } =
    usePaginatedQueryExtraData<boolean>(numTotalItems, false);

  const setDirtyStatusAndRefresh = (index: number, status: boolean) => {
    setDirtyStatus(index, status);
    listRef.current?.forceUpdate();
  };

  useEffect(() => {
    const handler = () => {
      setInnerHeight(window.innerHeight);
    };
    window.addEventListener("resize", handler);
    return () => {
      window.removeEventListener("resize", handler);
    };
  }, []);

  useEffect(() => {
    if (startFileId) {
      getApis()
        .loadApi.getLoadIdxOfFileLoadGetLoadIndexPost({
          getIdxOfFileReqeust: { fileId: startFileId },
        })
        .then((res) => {
          setItemToScrollIdx(res.idx);
        });
    }
  }, [startFileId]);

  useLayoutEffect(() => {
    if (itemToScrollIdx !== 0 && loaded && listRef.current) {
      listRef.current.scrollToItem(itemToScrollIdx, "center");
    }
  }, [loaded, itemToScrollIdx]);

  return (
    <Container sx={{ mt: 2 }}>
      {!loaded ? (
        <Box>loading</Box>
      ) : (
        <FixedSizeList
          ref={listRef}
          height={innerHeight - 22}
          itemCount={numTotalItems}
          itemSize={400}
          width={1200}
          className="customScrollBar"
          overscanCount={20}
        >
          {({ index, style }) => {
            const item = getItem(index);
            return (
              <div style={{ ...style }}>
                <div
                  style={{
                    width: "100%",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                  }}
                >
                  <Box
                    sx={{
                      border: `1px solid ${
                        getDirtyStatus(index) ? "red" : "black"
                      }`,
                      p: 2,
                      m: 1,
                      display: "flex",
                      flexDirection: "row",
                      alignItems: "center",
                      width: "90%",
                    }}
                  >
                    <FileView
                      file={item}
                      playable
                      onDoubleClick={() => {
                        if (item) {
                          openFileMutation(item);
                        }
                      }}
                      showMenu={false}
                    />

                    <Box
                      sx={{
                        ml: 5,
                        width: "50%",
                        color: "white",
                      }}
                    >
                      <TextField
                        multiline
                        fullWidth
                        minRows={4}
                        maxRows={7}
                        color="primary"
                        inputProps={{
                          style: { color: "#eee" },
                        }}
                        value={item?.description}
                        onChange={(e) => {
                          const it = getItem(index);
                          setDirtyStatusAndRefresh(index, true);
                          if (it) {
                            it.description = e.target.value;
                            listRef.current?.forceUpdate();
                          }
                        }}
                      />
                    </Box>

                    <Button
                      sx={{ ml: 5, width: "120px", p: 1 }}
                      variant="contained"
                      onClick={() => {
                        if (item) {
                          getApis()
                            .metadataApi.updateDescriptionMetadatadescriptionPost(
                              {
                                updateDescriptionRequest: {
                                  fileId: item.id,
                                  description: item.description,
                                },
                              }
                            )
                            .then(() => {
                              setDirtyStatusAndRefresh(index, false);
                            });
                        }
                      }}
                    >
                      Update
                    </Button>
                  </Box>
                </div>
              </div>
            );
          }}
        </FixedSizeList>
      )}
    </Container>
  );
};
