import { Box, Button, Container, TextField } from "@mui/material";
import { useMutation, useQuery } from "@tanstack/react-query";
import { FileView } from "../../components/FileView";
import { FileInfo } from "../../utils/model";

export const MetadataEditor = () => {
  const query = useQuery<FileInfo[]>({
    queryKey: ["idk"],
    queryFn: async () => {
      return await fetch("http://0.0.0.0:8000/files-testing").then((x) =>
        x.json()
      );
    },
  });

  const openFileMutation = useMutation({
    mutationFn: async (fileName: string) => {
      const resp = await fetch("http://0.0.0.0:8000/open", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          file_name: fileName,
        }),
      }).then((x) => x.json());
      console.log(resp);
    },
    onSuccess: () => {
      console.log("done");
    },
  });

  return (
    <Container>
      {query.isLoading ? (
        <Box>loading</Box>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column" }}>
          {query.data?.map((item) => {
            return (
              <Box
                key={item.name}
                sx={{
                  border: "1px solid black",
                  p: 2,
                  m: 1,
                  display: "flex",
                  flexDirection: "row",
                  alignItems: "center",
                  width: "100%",
                }}
              >
                <FileView
                  file={item}
                  playable
                  onDoubleClick={() => {
                    openFileMutation.mutate(item.name);
                  }}
                />

                <Box
                  sx={{
                    ml: 5,
                    width: "50%",
                    color: "white",
                  }}
                >
                  <TextField
                    multiline
                    fullWidth
                    minRows={4}
                    maxRows={7}
                    color="primary"
                    inputProps={{
                      style: { color: "#eee" },
                    }}
                  />
                </Box>

                <Button
                  sx={{ ml: 5, width: "120px", p: 1 }}
                  variant="contained"
                >
                  Update
                </Button>
              </Box>
            );
          })}
        </Box>
      )}
    </Container>
  );
};
