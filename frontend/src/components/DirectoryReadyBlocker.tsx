import { Box, CircularProgress, Typography } from "@mui/material";
import {
  Fragment,
  PropsWithChildren,
  useContext,
  useEffect,
  useState,
} from "react";
import { getApis } from "../api/initializeApis";
import { SelectedDirectoryContext } from "../utils/directoryctx";

const RETRY_PERIOD_MS = 500;

export const DirectoryReadyBlocker = ({ children }: PropsWithChildren<{}>) => {
  const directory = useContext(SelectedDirectoryContext);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const checkIfReady = () => {
      getApis()
        .directoriesApi.listRegisteredDirectoriesDirectoryGet()
        .then((directories) => {
          const dir = directories.find((x) => x.name === directory);
          let shouldRetry = false;
          if (dir != null) {
            if (dir.ready) {
              setReady(true);
            } else if (dir.failed) {
              setFailed(true);
            } else {
              shouldRetry = true;
            }
          } else {
            shouldRetry = true;
          }
          if (shouldRetry) {
            setTimeout(checkIfReady, RETRY_PERIOD_MS);
          }
        })
        .catch((err) => {
          console.error(err);
          setTimeout(checkIfReady, RETRY_PERIOD_MS);
        });
    };
    checkIfReady();
  }, [directory]);

  return ready ? (
    <Fragment>{children}</Fragment>
  ) : (
    <Box
      sx={{
        display: "flex",
        flexDirection: "row",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
      }}
    >
      {failed ? (
        <Box>Directory initialization failed, check server logs.</Box>
      ) : (
        <Box>
          <Typography>
            Initializing directory, this will take some time, you can close this
            window, no need to refresh it.
          </Typography>
          <Box sx={{ display: "flex", justifyContent: "center" }}>
            <CircularProgress
              sx={{ minWidth: "80px", minHeight: "80px", mt: 5 }}
            />
          </Box>
        </Box>
      )}
    </Box>
  );
};
