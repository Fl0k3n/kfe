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
