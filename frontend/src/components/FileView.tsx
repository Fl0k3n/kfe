import { Box } from "@mui/material";
import "../index.css";
import { FileInfo } from "../utils/model";

type Props = {
  file: FileInfo;
  playable?: boolean;
  showName?: boolean;
  width?: number;
  height?: number;
  onDoubleClick?: () => void;
};

export const FileView = ({
  file,
  playable = true,
  showName = true,
  width = 300,
  height = 300,
  onDoubleClick,
}: Props) => {
  return (
    <Box
      sx={{
        display: "flex",
        alignContent: "center",
      }}
    >
      <Box>
        <Box
          className={`fileContainer${playable ? " playableFileContainer" : ""}`}
          sx={{
            position: "relative",
            height: `${width}px`,
            width: `${height}px`,
          }}
        >
          <img
            onDoubleClick={onDoubleClick}
            style={{
              height: `${width}px`,
              width: `${height}px`,
            }}
            src={`data:image/jpeg;base64, ${file.thumbnail}`}
            alt={file.name}
          ></img>
          {playable && file.type === "video" && (
            <div className="fileTriangle" />
          )}
          <Box />
        </Box>
        {showName && (
          <Box
            sx={{
              textAlign: "center",
              mt: 1,
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textWrap: "nowrap",
              width: "300px",
            }}
          >
            {file.name}
          </Box>
        )}
      </Box>
    </Box>
  );
};
