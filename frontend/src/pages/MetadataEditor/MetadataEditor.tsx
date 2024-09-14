import { Box, Button, Container, TextField } from "@mui/material";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { FixedSizeList } from "react-window";
import { getApis } from "../../api/initializeApis";
import { FileView } from "../../components/FileView";

export const MetadataEditor = () => {
  //   const queryClient = useQueryClient();
  const filesQuery = useQuery({
    queryKey: ["idk"],
    queryFn: () => getApis().loadApi.getDirectoryFilesLoadGet(),
  });

  const openFileMutation = useMutation({
    mutationFn: (fileName: string) =>
      getApis().accessApi.openFileAccessOpenPost({
        openFileRequest: { fileName },
      }),
  });

  const updateDescriptionMutation = useMutation({
    mutationFn: (x: { id: number; description: string }) =>
      getApis().metadataApi.updateDescriptionMetadatadescriptionPost({
        updateDescriptionRequest: { fileId: x.id, description: x.description },
      }),
    onSuccess: () => {
      //   queryClient.invalidateQueries({ queryKey: ["idk"] });
    },
  });

  const [descriptions, setDescriptions] = useState<string[]>([]);
  useEffect(() => {
    if (filesQuery.isSuccess) {
      setDescriptions(filesQuery.data.files.map((x) => x.description));
    }
  }, [filesQuery.isSuccess, filesQuery.data]);

  return (
    <Container>
      {filesQuery.isLoading ? (
        <Box>loading</Box>
      ) : (
        <FixedSizeList
          height={1200}
          itemCount={filesQuery.data?.files.length ?? 0}
          itemSize={150}
          width={800}
        >
          {({ index }) => (
            <Box
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
                file={filesQuery.data?.files[index]}
                playable
                onDoubleClick={() => {
                  openFileMutation.mutate(
                    filesQuery.data?.files[index].name ?? ""
                  );
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
                  value={descriptions[index]}
                  onChange={(e) => {
                    setDescriptions((old) => {
                      const oldCopy = [...old];
                      oldCopy[index] = e.target.value;
                      return oldCopy;
                    });
                  }}
                />
              </Box>

              <Button
                sx={{ ml: 5, width: "120px", p: 1 }}
                variant="contained"
                onClick={() => {
                  updateDescriptionMutation.mutate({
                    id: filesQuery.data?.files[index].id ?? 0,
                    description: descriptions[index],
                  });
                }}
              >
                Update
              </Button>
            </Box>
          )}
        </FixedSizeList>
      )}
    </Container>
  );
};
