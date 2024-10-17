import HandymanIcon from "@mui/icons-material/Handyman";
import { Box, Button, TextField, Typography } from "@mui/material";
import { useLayoutEffect, useState } from "react";

type Props = {
  name: string;
  value?: string;
  onValueChange: (newValue: string) => void;
  onUpdate: () => void;
  showFixedIcon?: boolean;
};

export const EditorTextItem = ({
  name,
  value,
  onValueChange,
  onUpdate,
  showFixedIcon = false,
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
          width: "130px",
          mr: 2,
        }}
      >
        <Typography variant="body1">{name}</Typography>
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
