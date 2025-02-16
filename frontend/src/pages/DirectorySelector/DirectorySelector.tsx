import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import FolderOpenIcon from "@mui/icons-material/FolderOpen";
import HelpIcon from "@mui/icons-material/Help";
import {
  Box,
  Button,
  Checkbox,
  Container,
  Divider,
  FormControl,
  Radio,
  RadioGroup,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { RegisterDirectoryRequest, RegisteredDirectoryDTO } from "../../api";
import { getApis } from "../../api/initializeApis";
import "../../index.css";
import { AVAILABLE_LANGUAGES } from "../../utils/constants";
type Props = {
  first: boolean;
  onSelected: (directory: RegisteredDirectoryDTO) => void;
  onGoBack: () => void;
};

export const DirectorySelector = ({ first, onSelected, onGoBack }: Props) => {
  const [directoryData, setDirectoryData] = useState<RegisterDirectoryRequest>({
    name: "",
    path: "",
    primaryLanguage: "en",
    shouldGenerateLlmDescriptions: false,
  });
  const [error, setError] = useState(false);
  const [pickerError, setPickerError] = useState(false);

  const registerDirectoryMutation = useMutation({
    mutationFn: () =>
      getApis().directoriesApi.registerDirectoryDirectoryPost({
        registerDirectoryRequest: directoryData,
      }),
    onError: (err) => {
      setError(true);
    },
    onSuccess: (res) => {
      setError(false);
      onSelected(res);
    },
  });

  const pickDirectoryMutation = useMutation({
    mutationFn: () =>
      getApis().accessApi.selectDirectoryAccessSelectDirectoryPost(),
    onError: (err) => {
      setPickerError(true);
    },
    onSuccess: (res) => {
      setPickerError(false);
      if (res.selectedPath != null) {
        setDirectoryData((x) => ({
          ...x,
          path: res.selectedPath!,
        }));
        if (directoryData.name === "") {
          const splitCharacter = res.selectedPath.includes("\\") ? "\\" : "/";
          setDirectoryData((x) => ({
            ...x,
            name:
              res.selectedPath!.substring(
                res.selectedPath!.lastIndexOf(splitCharacter) + 1
              ) ?? "",
          }));
        }
      } else if (!res.canceled) {
        setPickerError(true);
      }
    },
  });

  return (
    <Container>
      <Box
        component="form"
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 2,
          maxWidth: 800,
          margin: "auto",
          marginTop: "80px",
        }}
        noValidate
        autoComplete="off"
      >
        <Box sx={{ textAlign: "center", mb: 2 }}>
          {first ? (
            <Typography>
              Please select the first directory with files that you want to
              search, subdirectories will be ignored
            </Typography>
          ) : (
            <Typography>
              Please select new directory with files that you want to search,
              subdirectories will be ignored
            </Typography>
          )}
        </Box>

        <FormControl fullWidth>
          <Box display="flex" alignItems="center">
            <Typography sx={{ width: "200px", marginRight: 2, color: "#eee" }}>
              Path to directory
            </Typography>
            <Box sx={{ width: "70%" }}>
              <TextField
                inputProps={{ style: { color: "#fff" } }}
                variant="outlined"
                placeholder="Absolute directory path (e.g., /home/user/directory)"
                fullWidth
                value={directoryData.path}
                onChange={(e) => {
                  setDirectoryData({ ...directoryData, path: e.target.value });
                }}
              />
            </Box>
            <Button
              variant="contained"
              sx={{ width: "200px", ml: 2 }}
              disabled={pickDirectoryMutation.isPending}
              onClick={() => {
                pickDirectoryMutation.mutate();
              }}
            >
              Pick
              <FolderOpenIcon sx={{ ml: 1 }} />
            </Button>
          </Box>
        </FormControl>

        <FormControl fullWidth>
          <Box display="flex" alignItems="center">
            <Typography sx={{ width: "200px", marginRight: 2, color: "#eee" }}>
              Name of directory
            </Typography>
            <TextField
              inputProps={{ style: { color: "#fff" } }}
              variant="outlined"
              placeholder="Directory name (anything you like)"
              fullWidth
              value={directoryData.name}
              onChange={(e) => {
                setDirectoryData({ ...directoryData, name: e.target.value });
              }}
            />
          </Box>
        </FormControl>

        <Divider />
        <Box
          sx={{ display: "flex", flexDirection: "row", alignItems: "center" }}
        >
          <Typography>Select primary</Typography>
          <Tooltip
            title={
              "Some features are language specific (e.g., text embeddings), application also allows you to manually describe files." +
              "You should select the language in which you want to write these descriptions (and later search across them) and in which words in majority of your audio files are spoken."
            }
            placement="top-start"
          >
            <HelpIcon
              sx={{ ml: 0.1, fontSize: "14px", mr: 0.5, mb: 1 }}
              className="helpTooltipIcon"
            />
          </Tooltip>
          language:
        </Box>
        <RadioGroup name="default-directory-radio-group">
          {AVAILABLE_LANGUAGES.map((language) => (
            <Box
              key={language}
              sx={{
                display: "flex",
                flexDirection: "row",
                alignItems: "center",
                mb: 1,
              }}
            >
              <Radio
                checked={directoryData.primaryLanguage === language}
                onClick={() => {
                  setDirectoryData({
                    ...directoryData,
                    primaryLanguage: language,
                  });
                }}
              />
              <Typography>{language}</Typography>
            </Box>
          ))}
        </RadioGroup>

        <FormControl fullWidth>
          <Box display="flex" alignItems="center">
            <Checkbox
              sx={{ ml: -1.25 }}
              defaultChecked={directoryData.shouldGenerateLlmDescriptions}
              onChange={(event) => {
                setDirectoryData({
                  ...directoryData,
                  shouldGenerateLlmDescriptions: event.target.checked,
                });
              }}
            />
            <Typography sx={{ color: "#eee" }}>
              Generate additional searchable descriptions using LLM with vision
              capabilities
            </Typography>
            <Tooltip
              title={
                "If you toggle it, vision LLM will be used (DeepSeek Janus Pro 1B). This model weights over 4GB and requires decent GPU (or Apple Silicon and some patience) . You will be able to use @llm tag to search for images and videos based on generated descriptions. Results, however, may not be worth additional processing time and resources (it can take a few seconds to process a single file!). CLIP search already works very well for visual searches. If unsure - leave unset or try it out on some small directory. You can always change this setting by untracking directory and adding it again."
              }
              placement="top-start"
            >
              <HelpIcon
                sx={{ ml: 0.5, fontSize: "14px", mr: 0.5, mb: 1 }}
                className="helpTooltipIcon"
              />
            </Tooltip>
          </Box>
        </FormControl>

        {/* <Divider />
        <Typography>Select languages that OCR should detect:</Typography>

        {AVAILABLE_LANGUAGES.map((lang) => (
          <FormControl key={lang}>
            <FormControlLabel
              control={<Checkbox />}
              label={lang}
              checked={
                directoryData.languages.find((x) => x === lang) !== undefined
              }
              onChange={(e) => {
                const exists =
                  directoryData.languages.find((x) => x === lang) !== undefined;
                setDirectoryData({
                  ...directoryData,
                  languages: exists
                    ? directoryData.languages.filter((x) => x !== lang)
                    : [...directoryData.languages, lang],
                });
              }}
              labelPlacement="start"
              sx={{
                marginLeft: 0,
                marginRight: "auto",
              }}
            />
          </FormControl>
        ))} */}
        <Button
          sx={{ width: "50%", margin: "auto" }}
          variant="contained"
          disabled={
            directoryData.name === "" ||
            directoryData.path === "" ||
            registerDirectoryMutation.isPending
          }
          onClick={() => registerDirectoryMutation.mutate()}
        >
          Select Directory
        </Button>
        {(error || pickerError) && (
          <Box sx={{ mt: 2, color: "red" }}>
            {error
              ? "Failed to select directory, make sure you pasted absolute path to directory and that path exists, see server logs for more info."
              : "Failed to run native directory picker, please enter the path manually."}
          </Box>
        )}
      </Box>
      {!first && (
        <Box
          sx={{
            position: "fixed",
            bottom: "20px",
            left: "20px",
          }}
        >
          <ArrowBackIcon onClick={onGoBack} className="menuIcon" />
        </Box>
      )}
    </Container>
  );
};
