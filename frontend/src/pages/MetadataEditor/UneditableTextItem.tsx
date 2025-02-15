import HelpIcon from "@mui/icons-material/Help";
import { Box, TextField, Tooltip, Typography } from "@mui/material";
import "../../index.css";

type Props = {
  name: string;
  value?: string;
  helpInfo?: string;
};

export const UneditableTextItem = ({ name, value, helpInfo }: Props) => {
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
      </Box>
      <Box
        sx={{
          width: "90%",
          color: "white",
        }}
      >
        <TextField
          multiline
          fullWidth
          rows={5}
          color="primary"
          inputProps={{
            readOnly: true,
            style: { color: "#eee" },
          }}
          value={value}
        />
      </Box>
    </Box>
  );
};
