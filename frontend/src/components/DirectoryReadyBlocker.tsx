import HelpIcon from "@mui/icons-material/Help";
import {
  Box,
  Button,
  CircularProgress,
  Tooltip,
  Typography,
} from "@mui/material";
import { Fragment, PropsWithChildren } from "react";
import { RegisteredDirectoryDTO } from "../api";
import { getApis } from "../api/initializeApis";

type Props = {
  directoryData?: RegisteredDirectoryDTO;
};

export const DirectoryReadyBlocker = ({
  directoryData,
  children,
}: PropsWithChildren<Props>) => {
  return directoryData?.ready ? (
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
      {directoryData?.failed ? (
        <Box sx={{ maxWidth: "700px" }}>
          Directory initialization failed. Download might have failed for some
          model, try untracking the directory using button in the top left
          corner, then add it again. Check server logs for more information,
          last status: {directoryData.initProgressDescription}
        </Box>
      ) : (
        <Box>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <Typography>
              Initializing directory and downloading necessary AI models, this
              will take some time, you can close this window, no need to refresh
              it.
            </Typography>
            <Box sx={{ display: "flex", justifyContent: "center" }}>
              <CircularProgress
                sx={{ minWidth: "80px", minHeight: "80px", mt: 5 }}
                variant="determinate"
                value={(directoryData?.initProgress ?? 0) * 100}
              />
            </Box>
            <Typography sx={{ mt: 2 }}>
              {directoryData?.initProgressDescription}
            </Typography>
          </Box>
          <Box sx={{ display: "flex", justifyContent: "center" }}>
            <Tooltip title="Progress will be lost, but directory won't be unregistered (if you restart the application initialization will be attempted again, if you don't want that to happen use button in top left corner to stop tracking after cancelling). Cancellation is a best-effort operation, it might not happen immediately. Only directory that is currently progressing (and not queued) can be cancelled, so if you are initializing multiple, make sure to cancel the progressing one first. Feel free to click this multiple times, it might help.">
              <Button
                sx={{ mt: 20 }}
                variant="contained"
                color="secondary"
                size="large"
                disabled={directoryData?.name == null}
                onClick={() => {
                  getApis().directoriesApi.cancelInitializationDirectoryCancelInitializationDirectoryNamePost(
                    { directoryName: directoryData?.name ?? "" }
                  );
                }}
              >
                cancel
                <HelpIcon
                  sx={{ ml: 0.1, mb: 0.5, fontSize: "14px" }}
                  className="helpTooltipIcon"
                />
              </Button>
            </Tooltip>
          </Box>
        </Box>
      )}
    </Box>
  );
};
