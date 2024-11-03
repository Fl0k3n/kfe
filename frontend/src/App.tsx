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
import {
  getDefaultDir,
  SelectedDirectoryContext,
  setDefaultDir,
} from "./utils/directoryctx";

type View = "viewer" | "metadata-editor" | "directory-selector" | "loading";

const CHECK_FOR_STATUS_UPDATES_PERIOD = 200;

function App() {
  const [directory, setDirectory] = useState<string | null>(null);
  const [view, setView] = useState<View>("loading");
  const [startFileId, setStartFileId] = useState<number | undefined>(undefined);
  const queryClient = useQueryClient();
  const statusChecker = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { isSuccess, data: directories } = useQuery({
    queryKey: ["directories"],
    queryFn: () =>
      getApis().directoriesApi.listRegisteredDirectoriesDirectoryGet(),
    retry: true,
    retryDelay: 500,
  });

  useEffect(() => {
    if (isSuccess) {
      getApis().eventsApi.onUiOpenedOrRefreshedEventsOpenedOrRefreshedPost();
    }
  }, [isSuccess]);

  useEffect(() => {
    if (directories == null || statusChecker.current != null) {
      return;
    }
    const progressingDir = directories.find((x) => !x.failed && !x.ready);
    if (progressingDir == null) {
      return;
    }
    const checkForStatusUpdates = () => {
      getApis()
        .directoriesApi.listRegisteredDirectoriesDirectoryGet()
        .then((updatedDirs) => {
          if (updatedDirs.length === 0) {
            setView("loading");
            setDirectory("");
          } else if (updatedDirs.find((x) => x.name === directory) == null) {
            setDirectory(updatedDirs[0].name);
          } else if (updatedDirs.find((x) => !x.failed && !x.ready) != null) {
            statusChecker.current = setTimeout(
              checkForStatusUpdates,
              CHECK_FOR_STATUS_UPDATES_PERIOD
            );
          } else {
            statusChecker.current = null;
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

    checkForStatusUpdates();

    return () => {
      if (statusChecker.current != null) {
        clearTimeout(statusChecker.current);
      }
    };
  }, [directories, queryClient, directory]);

  useEffect(() => {
    if (isSuccess && view === "loading") {
      if (directories.length > 0) {
        const defaultDir = getDefaultDir();
        let selectedDir = undefined;
        if (defaultDir != null) {
          selectedDir = directories.find((x) => x.name === defaultDir)?.name;
        }
        setDirectory(selectedDir ?? directories[0].name);
        setView("viewer");
      } else {
        setView("directory-selector");
      }
    }
  }, [isSuccess, directories, view]);

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
          setView("loading");
          setDirectory("");
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
        onBack={() => setView("viewer")}
      />
    );
  }

  return (
    <SelectedDirectoryContext.Provider value={directory}>
      <DirectoryReadyBlocker>
        {view === "metadata-editor" && (
          <MetadataEditor startFileId={startFileId} />
        )}
        {view === "viewer" && (
          <FileViewer
            onNavigateToDescription={(x) => {
              setStartFileId(x);
              setView("metadata-editor");
            }}
          />
        )}
        <ViewIcon
          className="menuIcon"
          onClick={() => {
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
          setDirectory(directory.name);
        }}
        onStopTrackingDirectory={(directoryToRemove) => {
          if (directoryToRemove.name === directory) {
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
