import EditIcon from "@mui/icons-material/Edit";
import FolderIcon from "@mui/icons-material/Folder";
import { Box, CircularProgress, Typography } from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { RegisteredDirectoryDTO } from "./api";
import { getApis } from "./api/initializeApis";
import { DirectoryReadyBlocker } from "./components/DirectoryReadyBlocker";
import { DirectorySwitcher } from "./components/DirectorySwitcher";
import { Help } from "./components/Help";
import "./index.css";
import { DirectorySelector } from "./pages/DirectorySelector/DirectorySelector";
import { FileViewer } from "./pages/FileViewer/FileViewer";
import { MetadataEditor } from "./pages/MetadataEditor/MetadataEditor";
import { NavigationContext } from "./utils/commonTypes";
import { CHECK_FOR_STATUS_UPDATES_PERIOD } from "./utils/constants";
import {
  getDefaultDir,
  SelectedDirectoryContext,
  setDefaultDir,
} from "./utils/directoryctx";
import { HistoryStack } from "./utils/history";

type View = "viewer" | "metadata-editor" | "directory-selector" | "loading";

function App() {
  const [directory, setDirectory] = useState<string | null>(null);
  const [navigationContext, setNavigationContext] =
    useState<NavigationContext | null>(null);
  const [view, setView] = useState<View>("loading");
  const [startFileId, setStartFileId] = useState<number | undefined>(undefined);
  const queryClient = useQueryClient();
  const statusChecker = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [historyStack, setHistoryStack] = useState(new HistoryStack());

  const { isSuccess, data: directories } = useQuery({
    queryKey: ["directories"],
    queryFn: () =>
      getApis().directoriesApi.listRegisteredDirectoriesDirectoryGet(),
    retry: true,
    retryDelay: 500,
  });

  useEffect(() => {
    if (directories == null || statusChecker.current != null) {
      return;
    }
    const progressingDir = directories.find((x) => !x.failed && !x.ready);
    if (progressingDir == null) {
      return;
    }
    const checkForStatusUpdates = () => {
      if (statusChecker.current == null) return;
      getApis()
        .directoriesApi.listRegisteredDirectoriesDirectoryGet()
        .then((updatedDirs) => {
          statusChecker.current = null;
          if (updatedDirs.length === 0) {
            setView("loading");
            setDirectory(null);
          } else if (updatedDirs.find((x) => !x.failed && !x.ready) != null) {
            statusChecker.current = setTimeout(
              checkForStatusUpdates,
              CHECK_FOR_STATUS_UPDATES_PERIOD
            );
          }
          queryClient.setQueryData(["directories"], updatedDirs);
        })
        .catch(() => {
          statusChecker.current = setTimeout(
            checkForStatusUpdates,
            CHECK_FOR_STATUS_UPDATES_PERIOD
          );
        });
    };

    statusChecker.current = setTimeout(
      checkForStatusUpdates,
      CHECK_FOR_STATUS_UPDATES_PERIOD
    );

    return () => {
      if (statusChecker.current != null) {
        clearTimeout(statusChecker.current);
        statusChecker.current = null;
      }
    };
  }, [directories, queryClient, directory]);

  useEffect(() => {
    if (isSuccess && view === "loading") {
      if (directories.length > 0) {
        if (directory == null) {
          const defaultDir = getDefaultDir();
          let selectedDir = undefined;
          if (defaultDir != null) {
            selectedDir = directories.find((x) => x.name === defaultDir)?.name;
          }
          setDirectory(selectedDir ?? directories[0].name);
        }
        setView("viewer");
      } else {
        setView("directory-selector");
      }
    }
  }, [directory, isSuccess, directories, view]);

  useEffect(() => {
    setHistoryStack(new HistoryStack());
  }, [directory]);

  const unregisterDirectoryMutation = useMutation({
    mutationFn: (directory: RegisteredDirectoryDTO) =>
      getApis().directoriesApi.unregisterDirectoryDirectoryDelete({
        unregisterDirectoryRequest: { name: directory.name },
      }),
    onError: (err) => {
      queryClient.invalidateQueries({ queryKey: ["directories"] });
      setView("loading");
    },
    onSuccess: (res, input) => {
      if (isSuccess && directories) {
        const newDirectories = directories.filter((x) => x.name !== input.name);
        queryClient.setQueryData(["directories"], newDirectories);
        if (newDirectories.length === 0) {
          setView("directory-selector");
          setDirectory(null);
        }
      }
    },
    throwOnError: false,
  });

  const ViewIcon = view === "viewer" ? EditIcon : FolderIcon;

  if (view === "loading") {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        <CircularProgress sx={{ minWidth: "80px", minHeight: "80px", mt: 5 }} />
        <Typography sx={{ mt: 2 }}>
          Can't connect to file explorer server, it can be still initializing or
          crashed. If some watched directory has many new files initialization
          may take few minutes.
        </Typography>
      </Box>
    );
  }

  if (view === "directory-selector") {
    return (
      <DirectorySelector
        first={directories?.length === 0}
        onSelected={(dirData) => {
          if (directories?.length === 0) {
            setDefaultDir(dirData.name);
            setDirectory(dirData.name);
            queryClient.setQueryData(["directories"], [dirData]);
          } else {
            queryClient.setQueryData(
              ["directories"],
              [...directories!, dirData]
            );
          }
          setView("viewer");
        }}
        onGoBack={() => setView("viewer")}
      />
    );
  }

  return (
    <SelectedDirectoryContext.Provider value={directory}>
      <DirectoryReadyBlocker
        directoryData={directories?.find((x) => x.name === directory)}
      >
        {view === "metadata-editor" && (
          <MetadataEditor
            startFileId={startFileId}
            onGoBack={
              navigationContext == null
                ? undefined
                : () => {
                    setView("viewer");
                  }
            }
          />
        )}
        {view === "viewer" && (
          <FileViewer
            scrollToIdx={navigationContext?.navigatedFromViewIdx}
            initialSearchQuery={navigationContext?.searchQuery}
            initialDataSource={navigationContext?.dataSource}
            initialEmbeddingSimilarityItems={
              navigationContext?.embeddingSimilarityItems
            }
            historyStack={historyStack}
            onNavigateToDescription={(
              fileId,
              idx,
              currentSearchQuery,
              currentDataSource,
              embeddingSimilarityItems
            ) => {
              setStartFileId(fileId);
              setNavigationContext({
                navigatedFromViewIdx: idx,
                searchQuery: currentSearchQuery,
                dataSource: currentDataSource,
                embeddingSimilarityItems,
              });
              setView("metadata-editor");
            }}
          />
        )}
        <ViewIcon
          className="menuIcon"
          onClick={() => {
            setNavigationContext(null);
            setStartFileId(undefined);
            setView((view) =>
              view === "viewer" ? "metadata-editor" : "viewer"
            );
          }}
          sx={{
            position: "fixed",
            bottom: "20px",
            left: "20px",
          }}
        ></ViewIcon>
        <Help />
      </DirectoryReadyBlocker>
      <DirectorySwitcher
        directories={directories!}
        selectedDirectory={directory!}
        onAddDirectory={() => {
          setView("directory-selector");
        }}
        onSwitch={(directory) => {
          setNavigationContext(null);
          setDirectory(directory.name);
          setStartFileId(undefined);
        }}
        onStopTrackingDirectory={(directoryToRemove) => {
          if (directoryToRemove.name === directory) {
            setNavigationContext(null);
            if (directories!.length > 1) {
              const directoryToSwitchTo = directories?.find(
                (x) => x.name !== directory
              );
              setDirectory(directoryToSwitchTo!.name);
            }
          }
          unregisterDirectoryMutation.mutate(directoryToRemove);
        }}
      />
    </SelectedDirectoryContext.Provider>
  );
}

export default App;
