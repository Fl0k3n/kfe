import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import HelpIcon from "@mui/icons-material/Help";
import {
  Box,
  Checkbox,
  CircularProgress,
  Container,
  FormControlLabel,
  Switch,
  Tooltip,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import {
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
import { METADATA_ITEMS_FETCH_LIMIT } from "../../utils/constants";
import { SelectedDirectoryContext } from "../../utils/directoryctx";
import { useOpenFileMutation } from "../../utils/mutations";
import {
  useAllFilesProvider,
  usePaginatedQuery,
  usePaginatedQueryExtraData,
} from "../../utils/queries";
import { EditorTextItem } from "./EditorTextItem";
import { UneditableTextItem } from "./UneditableTextItem";
type Props = {
  startFileId?: number;
  onGoBack?: () => void;
};

export const MetadataEditor = ({ startFileId, onGoBack }: Props) => {
  const directory = useContext(SelectedDirectoryContext) ?? "";
  const [innerHeight, setInnerHeight] = useState(window.innerHeight);
  const [itemToScrollIdx, setItemToScrollIdx] = useState(0);
  const [showLLMDescriptions, setShowLLMDescriptions] = useState(false);
  const listRef = useRef<FixedSizeList<any>>(null);
  const openFileMutation = useOpenFileMutation();
  const allFilesProvider = useAllFilesProvider(
    directory,
    METADATA_ITEMS_FETCH_LIMIT
  );
  const { loaded, numTotalItems, getItem } = usePaginatedQuery<FileMetadataDTO>(
    METADATA_ITEMS_FETCH_LIMIT,
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
        .filesApi.getFileOffsetInLoadResultsFilesGetOffsetInLoadResultsPost({
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

  const { isSuccess: loadedDirectoryMetadata, data: directoryMetadata } =
    useQuery({
      queryKey: ["directory", "metadata", directory],
      queryFn: () =>
        getApis().directoriesApi.getDirectoryMetadataDirectoryMetadatadaDirectoryNameGet(
          { directoryName: directory }
        ),
      enabled: directory !== "",
    });

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
          itemSize={450}
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
                      {showLLMDescriptions &&
                      loadedDirectoryMetadata &&
                      directoryMetadata.hasLlmDescriptions ? (
                        <UneditableTextItem
                          name="LLM Description"
                          value={item?.llmDescription ?? ""}
                          helpInfo="Description that was automatically generated by Large Language Model with vision capabilities. Updating is currently unsupported. You can regenerate all LLM descriptions using command line, refer to kfe --help."
                        />
                      ) : (
                        <>
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
                          {item?.fileType === "image" && (
                            <Box sx={{ ml: 1.5 }}>
                              <FormControlLabel
                                control={
                                  <Checkbox
                                    checked={item.isScreenshot}
                                    onChange={() => {
                                      const it = getItem(index);
                                      if (it) {
                                        getApis()
                                          .metadataApi.updateScreenshotTypeMetadataScreenshotPost(
                                            {
                                              updateScreenshotTypeRequest: {
                                                fileId: it.id,
                                                isScreenshot: !it.isScreenshot,
                                              },
                                              xDirectory: directory,
                                            }
                                          )
                                          .then(() => {
                                            it.isScreenshot = !it.isScreenshot;
                                            listRef.current?.forceUpdate();
                                          });
                                      }
                                    }}
                                  />
                                }
                                label="Image is screenshot"
                              ></FormControlLabel>
                              <Tooltip
                                title={
                                  "Screenshot is a file that contains some text. System sometimes fails to extract text from the" +
                                  " image and does not mark file as screenshot. You can correct this by toggling this checkbox."
                                }
                                placement="top-start"
                              >
                                <HelpIcon
                                  sx={{ ml: -1.5, fontSize: "14px" }}
                                  className="helpTooltipIcon"
                                />
                              </Tooltip>
                            </Box>
                          )}
                        </>
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
      {loadedDirectoryMetadata && directoryMetadata.hasLlmDescriptions && (
        <Box
          sx={{
            position: "fixed",
            bottom: "20px",
            right: "20px",
            display: "flex",
            alignItems: "center",
          }}
        >
          <Typography>LLM descriptions</Typography>
          <Switch
            defaultChecked={showLLMDescriptions}
            onChange={(event) => {
              setShowLLMDescriptions(event.target.checked);
            }}
          />
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
