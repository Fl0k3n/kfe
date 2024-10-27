import AddIcon from "@mui/icons-material/Add";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import MenuIcon from "@mui/icons-material/Menu";
import MenuOpenIcon from "@mui/icons-material/MenuOpen";
import SyncIcon from "@mui/icons-material/Sync";
import { Box, Button, Radio, RadioGroup, Typography } from "@mui/material";
import { useState } from "react";
import { RegisteredDirectoryDTO } from "../api";
import "../index.css";
import { getDefaultDir, setDefaultDir } from "../utils/directoryctx";

type Props = {
  selectedDirectory: string;
  directories: RegisteredDirectoryDTO[];
  onSwitch: (directory: RegisteredDirectoryDTO) => void;
  onAddDirectory: () => void;
};

export const DirectorySwitcher = ({
  selectedDirectory,
  directories,
  onSwitch,
  onAddDirectory,
}: Props) => {
  const [open, setOpen] = useState(false);
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
            maxHeight: "600px",
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
                <Radio
                  checked={directory.name === defaultDirectory}
                  onClick={() => {
                    if (directory.name !== defaultDirectory) {
                      setDefaultDir(directory.name);
                      setDefaultDirectory(directory.name);
                    }
                  }}
                />
                {directory.failed && <CloseIcon sx={{ color: "red" }} />}
                {directory.ready && <CheckIcon sx={{ color: "#15b800" }} />}
                {!directory.failed && !directory.ready && (
                  <SyncIcon sx={{ color: "#ad6eff" }} />
                )}
                <Button
                  variant="contained"
                  sx={{ ml: 1, width: "200px", maxWidth: "200px" }}
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
              </Box>
            ))}
          </RadioGroup>
          <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
            <Button variant="contained" onClick={onAddDirectory}>
              <AddIcon sx={{ mr: 1 }} />
              Add other
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
};
