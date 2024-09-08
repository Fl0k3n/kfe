import { Box, Button, Container, TextField } from "@mui/material";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
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
      setDescriptions(filesQuery.data.map((x) => x.description));
    }
  }, [filesQuery.isSuccess, filesQuery.data]);

  return (
    <Container>
      {filesQuery.isLoading ? (
        <Box>loading</Box>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column" }}>
          {filesQuery.data?.map((item, i) => {
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
                    value={descriptions[i]}
                    onChange={(e) => {
                      setDescriptions((old) => {
                        const oldCopy = [...old];
                        oldCopy[i] = e.target.value;
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
                      id: item.id,
                      description: descriptions[i],
                    });
                  }}
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
