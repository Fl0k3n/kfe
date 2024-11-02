import { Box, Menu, MenuItem } from "@mui/material";
import { useState } from "react";
import { FileMetadataDTO } from "../api/models";
import "../index.css";

export type MenuOption = {
  caption: string;
  handler: (file: FileMetadataDTO) => void;
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
}: Props) => {
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number;
    mouseY: number;
  } | null>(null);

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
              // TODO: copy file name to clipboard and trigger opening directory so we can ctrl+v filename to get file
              //   e.preventDefault();
              //   console.log("right click");
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
                        option.handler(file);
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
              <img
                style={{
                  maxHeight: `${width}px`,
                  maxWidth: `${height}px`,
                }}
                src={`data:image/jpeg;base64, ${file.thumbnailBase64}`}
                alt={file.name}
              />
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
