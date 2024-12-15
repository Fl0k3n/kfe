import { Box, CircularProgress, Typography } from "@mui/material";
import { Fragment, PropsWithChildren } from "react";
import { RegisteredDirectoryDTO } from "../api";

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
      )}
    </Box>
  );
};
