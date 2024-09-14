import { Box } from "@mui/material";
import { FileMetadataDTO } from "../api/models";
import "../index.css";

type Props = {
  file?: FileMetadataDTO;
  playable?: boolean;
  showName?: boolean;
  width?: number;
  height?: number;
  onDoubleClick?: () => void;
  onRightClick?: () => void;
};

export const FileView = ({
  file,
  playable = true,
  showName = true,
  width = 300,
  height = 300,
  onDoubleClick,
  onRightClick,
}: Props) => {
  return (
    <Box
      onDoubleClick={onDoubleClick}
      sx={{
        display: "flex",
        alignContent: "center",
      }}
    >
      <Box>
        {file ? (
          <Box
            className={`fileContainer${
              playable ? " playableFileContainer" : ""
            }`}
            sx={{
              position: "relative",
              width: `${width}px`,
              height: `${height}px`,
            }}
          >
            <img
              style={{
                height: `${width}px`,
                width: `${height}px`,
              }}
              onContextMenu={(e) => {
                // TODO: copy file name to clipboard and trigger opening directory so we can ctrl+v filename to get file
                //   e.preventDefault();
                //   console.log("right click");
                e.preventDefault();
                onRightClick?.();
              }}
              src={`data:image/jpeg;base64, ${file.thumbnailBase64}`}
              alt={file.name}
            />

            {playable && file.fileType === "video" && (
              <div className="fileTriangle" />
            )}
          </Box>
        ) : (
          <div
            style={{
              width: `${width}px`,
              height: `${height}px`,
            }}
          ></div>
        )}
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
            {file?.name ?? "loading"}
          </Box>
        )}
      </Box>
    </Box>
  );
};
