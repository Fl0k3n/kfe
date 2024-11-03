import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import {
  Box,
  Button,
  Checkbox,
  Container,
  Divider,
  FormControl,
  FormControlLabel,
  TextField,
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
    languages: AVAILABLE_LANGUAGES,
  });
  const [error, setError] = useState(false);

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
              search
            </Typography>
          ) : (
            <Typography>
              Please select new directory with files that you want to search
            </Typography>
          )}
        </Box>
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

        <FormControl fullWidth>
          <Box display="flex" alignItems="center">
            <Typography sx={{ width: "200px", marginRight: 2, color: "#eee" }}>
              Path to directory
            </Typography>
            <TextField
              inputProps={{ style: { color: "#fff" } }}
              variant="outlined"
              placeholder="Absolute directory path (copy from file explorer, e.g., /home/user/directory)"
              fullWidth
              value={directoryData.path}
              onChange={(e) => {
                setDirectoryData({ ...directoryData, path: e.target.value });
              }}
            />
          </Box>
        </FormControl>

        <Divider />
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
        ))}
        <Button
          sx={{ width: "50%", margin: "auto" }}
          variant="contained"
          disabled={
            directoryData.name === "" ||
            directoryData.path === "" ||
            directoryData.languages.length === 0 ||
            registerDirectoryMutation.isPending
          }
          onClick={() => registerDirectoryMutation.mutate()}
        >
          Select Directory
        </Button>
        {error && (
          <Box sx={{ mt: 2, color: "red" }}>
            Failed to select directory, make sure you pasted absolute path to
            directory and that path exists, see server logs for more info.
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
