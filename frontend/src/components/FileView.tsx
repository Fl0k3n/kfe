import AudioFileIcon from "@mui/icons-material/AudioFile";
import { Box, Menu, MenuItem, Typography } from "@mui/material";
import { useState } from "react";
import { FileMetadataDTO, FileType } from "../api/models";
import "../index.css";

export type MenuOption = {
  caption: string;
  handler: (file: FileMetadataDTO, idxWithinView: number) => void;
  hidden?: (file: FileMetadataDTO) => boolean;
};

type Props = {
  file?: FileMetadataDTO;
  playable?: boolean;
  showName?: boolean;
  width?: number;
  height?: number;
  onDoubleClick?: () => void;
  showMenu: boolean;
  menuOptions?: MenuOption[];
  idxWithinView?: number;
};

export const FileView = ({
  file,
  playable = true,
  showName = true,
  width = 300,
  height = 300,
  onDoubleClick,
  showMenu = false,
  menuOptions = [],
  idxWithinView = 0,
}: Props) => {
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number;
    mouseY: number;
  } | null>(null);

  const trimTooLongTextInTheMiddle = (fileName: string) => {
    const maxLength = width * 0.2;
    if (fileName.length <= maxLength) return fileName;
    const partLength = Math.floor((maxLength - 3) / 2);
    return fileName.slice(0, partLength) + "..." + fileName.slice(-partLength);
  };

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
            onContextMenu={(e) => {
              if (showMenu) {
                e.preventDefault();
                setContextMenu(
                  contextMenu === null
                    ? {
                        mouseX: e.clientX + 2,
                        mouseY: e.clientY - 6,
                      }
                    : null
                );
              }
            }}
          >
            {showMenu && (
              <Menu
                open={!!contextMenu}
                onClose={() => setContextMenu(null)}
                anchorReference="anchorPosition"
                anchorPosition={
                  contextMenu !== null
                    ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
                    : undefined
                }
              >
                {menuOptions
                  .filter((option) => !option.hidden?.(file))
                  .map((option) => (
                    <MenuItem
                      key={option.caption}
                      onClick={() => {
                        setContextMenu(null);
                        option.handler(file, idxWithinView);
                      }}
                    >
                      {option.caption}
                    </MenuItem>
                  ))}
              </Menu>
            )}
            <div
              style={{
                width: "100%",
                height: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {file.thumbnailBase64 === "" &&
              file.fileType !== FileType.Image ? (
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                  }}
                >
                  <AudioFileIcon
                    sx={{ width: width * 0.5, height: height * 0.5 }}
                  />
                  {!showName && (
                    <Typography
                      sx={{
                        maxWidth: width * 0.9,
                        maxHeight: height * 0.45,
                        textOverflow: "clip",
                        overflow: "hidden",
                        lineBreak: "anywhere",
                        wordBreak: "break-word",
                      }}
                    >
                      {trimTooLongTextInTheMiddle(file.name)}
                    </Typography>
                  )}
                </Box>
              ) : (
                <img
                  style={{
                    maxHeight: `${width}px`,
                    maxWidth: `${height}px`,
                  }}
                  src={`data:image/jpeg;base64, ${file.thumbnailBase64}`}
                  alt={file.name}
                />
              )}
            </div>

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
