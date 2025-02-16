import AddIcon from "@mui/icons-material/Add";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import DeleteIcon from "@mui/icons-material/Delete";
import MenuIcon from "@mui/icons-material/Menu";
import MenuOpenIcon from "@mui/icons-material/MenuOpen";
import SyncIcon from "@mui/icons-material/Sync";
import {
  Box,
  Button,
  Radio,
  RadioGroup,
  Tooltip,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { RegisteredDirectoryDTO } from "../api";
import "../index.css";
import { getDefaultDir, setDefaultDir } from "../utils/directoryctx";

type Props = {
  selectedDirectory: string;
  directories: RegisteredDirectoryDTO[];
  onSwitch: (directory: RegisteredDirectoryDTO) => void;
  onAddDirectory: () => void;
  onStopTrackingDirectory: (directory: RegisteredDirectoryDTO) => void;
};

export const DirectorySwitcher = ({
  selectedDirectory,
  directories,
  onSwitch,
  onAddDirectory,
  onStopTrackingDirectory,
}: Props) => {
  const [open, setOpen] = useState(false);
  const [deleteMode, setDeleteMode] = useState(false);
  const [defaultDirectory, setDefaultDirectory] = useState(getDefaultDir());

  const CurIcon = open ? MenuOpenIcon : MenuIcon;

  return (
    <Box sx={{ position: "fixed", top: "20px", left: "20px" }}>
      <Box
        sx={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
        }}
      >
        <CurIcon className="menuIcon" onClick={() => setOpen(!open)} />
        <Typography
          variant="h5"
          sx={{
            ml: 2,
            maxWidth: "250px",
            textOverflow: "ellipsis",
            color: "#eee",
          }}
        >
          {selectedDirectory}
        </Typography>
      </Box>
      {open && (
        <Box
          sx={{
            maxHeight: "800px",
            overflowY: "auto",
          }}
        >
          <RadioGroup name="default-directory-radio-group">
            {directories.map((directory) => (
              <Box
                key={directory.name}
                sx={{
                  display: "flex",
                  flexDirection: "row",
                  alignItems: "center",
                  mb: 1,
                }}
              >
                <Tooltip title={"Set as default"} placement="right">
                  <Radio
                    checked={directory.name === defaultDirectory}
                    onClick={() => {
                      if (directory.name !== defaultDirectory) {
                        setDefaultDir(directory.name);
                        setDefaultDirectory(directory.name);
                      }
                    }}
                  />
                </Tooltip>
                {directory.failed && (
                  <Tooltip title={"Initialization failed"} placement="right">
                    <CloseIcon sx={{ color: "red" }} />
                  </Tooltip>
                )}
                {directory.ready && (
                  <Tooltip title={"Directory ready"} placement="right">
                    <CheckIcon sx={{ color: "#15b800" }} />
                  </Tooltip>
                )}
                {!directory.failed && !directory.ready && (
                  <Tooltip
                    title={"Initialization in progress"}
                    placement="right"
                  >
                    <SyncIcon sx={{ color: "#ad6eff" }} />
                  </Tooltip>
                )}
                <Button
                  variant="contained"
                  sx={{
                    ml: 1,
                    width: "200px",
                    maxWidth: "200px",
                    textTransform: "none",
                  }}
                  disabled={selectedDirectory === directory.name}
                  onClick={() => onSwitch(directory)}
                >
                  <Typography
                    sx={{
                      textOverflow: "ellipsis",
                      maxWidth: "200px",
                      overflow: "hidden",
                    }}
                  >
                    {directory.name}
                  </Typography>
                </Button>
                {deleteMode && (
                  <DeleteIcon
                    className="stopTrackingIcon"
                    sx={{ ml: 1 }}
                    onClick={() => onStopTrackingDirectory(directory)}
                  />
                )}
              </Box>
            ))}
          </RadioGroup>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "left",
              ml: 6,
              mt: 2,
            }}
          >
            <Button
              variant="contained"
              onClick={onAddDirectory}
              sx={{ width: "200px" }}
            >
              <AddIcon sx={{ mr: 1 }} />
              Add Directory
            </Button>
            <Tooltip title="This operation doesn't delete any data, it only removes the directory from the list and stops watching for new or deleted files. If you add the directory again it will be immediately available for querying (if it already is). If you want to cleanup all metadata generated by this application then open the directory in your native file explorer and remove '.kfe.db', '.embeddings' and '.thumbnails'.">
              <Button
                variant="contained"
                color="secondary"
                onClick={() => {
                  setDeleteMode(!deleteMode);
                }}
                sx={{ mt: 2, width: "200px" }}
              >
                <DeleteIcon sx={{ mr: 1 }} />
                Stop Tracking
              </Button>
            </Tooltip>
          </Box>
        </Box>
      )}
    </Box>
  );
};
