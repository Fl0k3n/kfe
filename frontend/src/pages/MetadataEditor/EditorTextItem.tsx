import HandymanIcon from "@mui/icons-material/Handyman";
import HelpIcon from "@mui/icons-material/Help";
import { Box, Button, TextField, Tooltip, Typography } from "@mui/material";
import { useLayoutEffect, useState } from "react";
import "../../index.css";

type Props = {
  name: string;
  value?: string;
  helpInfo?: string;
  onValueChange: (newValue: string) => void;
  onUpdate: () => void;
  showFixedIcon?: boolean;
  updateDisabled?: boolean;
};

export const EditorTextItem = ({
  name,
  value,
  helpInfo,
  onValueChange,
  onUpdate,
  showFixedIcon = false,
  updateDisabled = false,
}: Props) => {
  const [multiline, setMultiline] = useState(false);
  useLayoutEffect(() => {
    setMultiline(true);
  }, []);
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "row",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          width: "160px",
          mr: 2,
        }}
      >
        <Box sx={{ display: "flex", flexDirection: "row" }}>
          <Typography variant="body1">{name}</Typography>
          {helpInfo && (
            <Tooltip title={helpInfo} placement="top-start">
              <HelpIcon
                sx={{ ml: 0.5, fontSize: "14px" }}
                className="helpTooltipIcon"
              />
            </Tooltip>
          )}
        </Box>
        {showFixedIcon && <HandymanIcon />}
      </Box>
      <Box
        sx={{
          width: "90%",
          color: "white",
        }}
      >
        <TextField
          multiline={multiline}
          fullWidth
          rows={5}
          color="primary"
          inputProps={{
            style: { color: "#eee" },
          }}
          value={value}
          onChange={(e) => {
            onValueChange(e.target.value);
          }}
        />
      </Box>

      <Button
        sx={{ ml: 5, width: "120px", p: 1 }}
        disabled={updateDisabled}
        variant="contained"
        onClick={() => {
          onUpdate();
        }}
      >
        Update
      </Button>
    </Box>
  );
};
