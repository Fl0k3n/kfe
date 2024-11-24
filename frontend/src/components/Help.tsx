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
      key: "clip",
      description:
        "search for images and videos similar to text query (text must be english, audio is ignored).",
    },
    {
      key: "lex",
      description:
        "lexical search across descriptions, OCRs and transcripts. More precise but returns fewer results.",
    },
    {
      key: "sem",
      description:
        "semantic search across descriptions, OCRs and transcripts. Less precise but returns more results.",
    },
    {
      key: "(d|o|t)lex",
      description:
        "lexical search across descriptions only (@dlex), ocrs or transcripts, respectively.",
    },
    {
      key: "(d|o|t)sem",
      description:
        "semantic search across descriptions only (@dsem), ocrs or transcripts, respectively.",
    },
  ];

  const fileTypeOptions: { key: string; description: string }[] = [
    { key: "image", description: "only images" },
    { key: "video", description: "only videos" },
    { key: "audio", description: "only audio" },
    { key: "ss", description: "only screenshot (image with text)" },
    { key: "!ss", description: "results without screenshots" },
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
        <Box sx={{ px: 2, py: 1, maxWidth: "1000px" }}>
          <Typography>
            Include options in the search query, example:{" "}
            <Highlight>@clip @image @!ss photo of a dog</Highlight>
          </Typography>
          <Typography>
            Combining different <Highlight>@</Highlight> options has "and"
            semantics, not "or".
          </Typography>
          <PaddedDivider />

          <List>
            <Typography>Filter file type:</Typography>
            <Box>
              <Typography>
                {fileTypeOptions.map((option, idx) => (
                  <span key={option.key}>
                    <Highlight>@{option.key}</Highlight>
                    {idx < fileTypeOptions.length - 1 && ", "}
                  </span>
                ))}
              </Typography>
              <Typography>
                to show: {fileTypeOptions.map((x) => x.description).join(", ")};{" "}
                {""}
                respectively.
              </Typography>
            </Box>
          </List>

          <PaddedDivider />

          <List>
            <Typography>
              Search algorithm selection, defaults to hybrid of all below
              (including <Highlight>@clip</Highlight> only if directory was
              marked as english):
            </Typography>
            {searchOptions.map((option) => (
              <ListItem key={option.key}>
                <Typography>
                  <Highlight>@{option.key}</Highlight> - {option.description}
                </Typography>
              </ListItem>
            ))}
            <Typography>
              <Highlight>Lexical</Highlight> means that search considers
              keywords, e.g., if you type "animal" and description was "a photo
              of dog" then it will not be matched (you will need to type "dog"
              explicitly). <Highlight>Semantic</Highlight> considers meaning of
              words, so for previous example, if you type "animal" that file
              should be matched. <Highlight>Clip</Highlight> uses AI model
              trained to understand what images represent, it works without
              annotating the data (no need for descriptions/ocrs/transcripts).
            </Typography>
          </List>

          <PaddedDivider />

          <List>
            <Typography>Other options:</Typography>
            <ListItem>
              <Typography>
                <Highlight>Right click</Highlight> any file to see more options,{" "}
                <Highlight>double click</Highlight> to open it in native viewer.
              </Typography>
            </ListItem>
            <ListItem>
              <Typography>
                <Highlight>Paste any image </Highlight>from clipboard to this
                page to find similar images.
              </Typography>
            </ListItem>
            <ListItem>
              <Typography>
                Click pen in <Highlight>bottom left</Highlight> corner to update
                descriptions for better search results.
              </Typography>
            </ListItem>
          </List>
        </Box>
      </Popover>
    </Box>
  );
};
