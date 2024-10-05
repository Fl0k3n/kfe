import HelpIcon from "@mui/icons-material/Help";
import {
  Box,
  Divider,
  List,
  ListItem,
  Popover,
  Typography,
} from "@mui/material";
import React, { useState } from "react";
import "../index.css";

export const Help = () => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  const handlePopoverOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handlePopoverClose = () => {
    setAnchorEl(null);
  };

  const searchOptions: { key: string; description: string }[] = [
    {
      key: "lex",
      description:
        "lexical (using raw words) search across descriptions, OCRs and transcripts. More precise but returns fewer results",
    },
    {
      key: "sem",
      description:
        "semantic (using semantic meaning of the query) search across descriptions, OCRs and transcripts. Less precise but returns more results",
    },
    {
      key: "dlex",
      description: "lexical search across descriptions",
    },
    {
      key: "olex",
      description: "lexical search across OCRs",
    },
    {
      key: "tlex",
      description: "lexical search across transcripts",
    },
    {
      key: "dsem",
      description: "semantic search across descriptions",
    },
    {
      key: "osem",
      description: "semantic search across OCRs",
    },
    {
      key: "tsem",
      description: "semantic search across transcripts",
    },
    {
      key: "clip",
      description:
        "clip search for images (find images similar to text query, text must be english)",
    },
  ];

  const fileTypeOptions: { key: string; description: string }[] = [
    { key: "image", description: "only images" },
    { key: "video", description: "only videos" },
    { key: "audio", description: "only audio" },
    { key: "ss", description: "only screenshot" },
    { key: "!ss", description: "without screenshots" },
  ];

  const Highlight = ({ children }: { children: string | React.ReactNode }) => (
    <span style={{ color: "#005e9c" }}>{children}</span>
  );
  const PaddedDivider = () => <Divider sx={{ my: 1 }} />;

  return (
    <Box sx={{ position: "fixed", top: "20px", right: "20px" }}>
      <Box onMouseEnter={handlePopoverOpen} onMouseLeave={handlePopoverClose}>
        <HelpIcon className="menuIcon" />
      </Box>
      <Popover
        sx={{ pointerEvents: "none" }}
        open={!!anchorEl}
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "left",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "left",
        }}
        onClose={handlePopoverClose}
        disableRestoreFocus
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography>
            Include filters in the search query, example:{" "}
            <Highlight>@clip @image @!ss photo of a dog</Highlight>
          </Typography>

          <PaddedDivider />

          <List>
            <Typography>Filter file type:</Typography>
            {fileTypeOptions.map((option) => (
              <ListItem key={option.key}>
                <Typography>
                  <Highlight>@{option.key}</Highlight> - {option.description}
                </Typography>
              </ListItem>
            ))}
          </List>

          <PaddedDivider />

          <List>
            <Typography>
              Search metric selection (defaults to <Highlight>@lex</Highlight>):
            </Typography>
            {searchOptions.map((option) => (
              <ListItem key={option.key}>
                <Typography>
                  <Highlight>@{option.key}</Highlight> - {option.description}
                </Typography>
              </ListItem>
            ))}
          </List>

          <PaddedDivider />

          <List>
            <Typography>Other options:</Typography>
            <ListItem>
              <Typography>
                <Highlight>Right click</Highlight> any file to see more options,{" "}
                <Highlight>double click</Highlight> to open it in native viewer
              </Typography>
            </ListItem>
            <ListItem>
              <Typography>
                <Highlight>Paste any image </Highlight>from clipboard to this
                page to find similar images
              </Typography>
            </ListItem>
            <ListItem>
              <Typography>
                Click pen in <Highlight>bottom left</Highlight> corner to update
                descriptions for better search results
              </Typography>
            </ListItem>
          </List>
        </Box>
      </Popover>
    </Box>
  );
};
