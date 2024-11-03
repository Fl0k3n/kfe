import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { Box, CircularProgress, Container, Typography } from "@mui/material";
import {
  useCallback,
  useContext,
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
import { SelectedDirectoryContext } from "../../utils/directoryctx";
import {
  useOpenFileMutation,
  usePaginatedQuery,
  usePaginatedQueryExtraData,
} from "../../utils/mutations";
import { EditorTextItem } from "./EditorTextItem";

const FETCH_LIMIT = 100;

type Props = {
  startFileId?: number;
  onGoBack?: () => void;
};

export const MetadataEditor = ({ startFileId, onGoBack }: Props) => {
  const directory = useContext(SelectedDirectoryContext) ?? "";
  const [innerHeight, setInnerHeight] = useState(window.innerHeight);
  const [itemToScrollIdx, setItemToScrollIdx] = useState(0);
  const openFileMutation = useOpenFileMutation();
  const listRef = useRef<FixedSizeList<any>>(null);
  const allFilesProvider = useCallback(
    (offset: number) => {
      return getApis()
        .loadApi.getDirectoryFilesLoadGet({
          offset,
          limit: FETCH_LIMIT,
          xDirectory: directory,
        })
        .then((x) => ({
          data: x.files,
          offset: x.offset,
          total: x.total,
        }));
    },
    [directory]
  );

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
        .loadApi.getOfFileOffsetInLoadResultsLoadGetOffsetInLoadResultsPost({
          getOffsetOfFileInLoadResultsRequest: { fileId: startFileId },
          xDirectory: directory,
        })
        .then((res) => {
          setItemToScrollIdx(res.idx);
        });
    } else {
      setItemToScrollIdx(0);
    }
  }, [startFileId, directory]);

  useLayoutEffect(() => {
    if (itemToScrollIdx !== 0 && loaded && listRef.current) {
      listRef.current.scrollToItem(itemToScrollIdx, "center");
    }
  }, [loaded, itemToScrollIdx]);

  return (
    <Container sx={{ mt: 2 }}>
      {!loaded ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <CircularProgress
            sx={{ minWidth: "80px", minHeight: "80px", mt: 5 }}
          />
        </Box>
      ) : numTotalItems > 0 ? (
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
                        mx: 5,
                        width: "100%",
                        display: "flex",
                        flexDirection: "column",
                        rowGap: "20px",
                      }}
                    >
                      <EditorTextItem
                        name="Description"
                        value={item?.description}
                        helpInfo="
                            Description can be arbitrary text which will be considered during search.
                            You can, for example, write names of visible objects or add some context with which you associate this file.
                        "
                        onValueChange={(val) => {
                          const it = getItem(index);
                          setDirtyStatusAndRefresh(index, true);
                          if (it) {
                            it.description = val;
                            listRef.current?.forceUpdate();
                          }
                        }}
                        onUpdate={() => {
                          if (item) {
                            getApis()
                              .metadataApi.updateDescriptionMetadataDescriptionPost(
                                {
                                  updateDescriptionRequest: {
                                    fileId: item.id,
                                    description: item.description,
                                  },
                                  xDirectory: directory,
                                }
                              )
                              .then(() => {
                                setDirtyStatusAndRefresh(index, false);
                              });
                          }
                        }}
                      />
                      {item?.isScreenshot && (
                        <EditorTextItem
                          name="OCR text"
                          value={item?.ocrText ?? ""}
                          helpInfo="
                          OCR (Optical Character Recognition) text is a text that was automatically extracted from image and is considered during search.
                          It does not have to be perfect for search to work reasonably, but if it is far from correct you may want to edit it manually.
                          "
                          onValueChange={(val) => {
                            const it = getItem(index);
                            setDirtyStatusAndRefresh(index, true);
                            if (it) {
                              it.ocrText = val;
                              listRef.current?.forceUpdate();
                            }
                          }}
                          onUpdate={() => {
                            if (item) {
                              getApis()
                                .metadataApi.updateOcrTextMetadataOcrPost({
                                  updateOCRTextRequest: {
                                    fileId: item.id,
                                    ocrText: item.ocrText!,
                                  },
                                  xDirectory: directory,
                                })
                                .then(() => {
                                  setDirtyStatusAndRefresh(index, false);
                                });
                            }
                          }}
                        />
                      )}
                      {item?.transcript != null && (
                        <EditorTextItem
                          name="Transcript"
                          value={item?.transcript}
                          helpInfo="
                          Transcript is text that was extracted automatically from audio or video file and is considered during search.
                          It does not have to be perfect for search to work reasonably, but if it is far from correct you may want to edit it manually.
                          "
                          showFixedIcon={!!item.isTranscriptFixed}
                          onValueChange={(val) => {
                            const it = getItem(index);
                            setDirtyStatusAndRefresh(index, true);
                            if (it) {
                              it.transcript = val;
                              listRef.current?.forceUpdate();
                            }
                          }}
                          onUpdate={() => {
                            if (item) {
                              getApis()
                                .metadataApi.updateTranscriptMetadataTranscriptPost(
                                  {
                                    updateTranscriptRequest: {
                                      fileId: item.id,
                                      transcript: item.transcript!,
                                    },
                                    xDirectory: directory,
                                  }
                                )
                                .then(() => {
                                  setDirtyStatusAndRefresh(index, false);
                                });
                            }
                          }}
                        />
                      )}
                    </Box>
                  </Box>
                </div>
              </div>
            );
          }}
        </FixedSizeList>
      ) : (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            justifyItems: "center",
            mt: 10,
          }}
        >
          <Typography>
            Directory is empty, this application does not allow adding files
            directly, use your native file explorer for that.
          </Typography>
        </Box>
      )}
      {onGoBack && (
        <Box
          sx={{
            position: "fixed",
            bottom: "80px",
            left: "20px",
          }}
        >
          <ArrowBackIcon onClick={onGoBack} className="menuIcon" />
        </Box>
      )}
    </Container>
  );
};
