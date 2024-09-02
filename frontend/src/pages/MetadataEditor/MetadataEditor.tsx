import { Box, Container } from "@mui/material";
import { useQuery } from "@tanstack/react-query";

type FileInfo = {
  name: string;
  thumbnail: string;
};

export const MetadataEditor = () => {
  const query = useQuery<FileInfo[]>({
    queryKey: ["idk"],
    queryFn: async () => {
      return await fetch("http://0.0.0.0:8000/files-testing").then((x) =>
        x.json()
      );
    },
  });

  return (
    <Container>
      {query.isLoading ? (
        <Box>loading</Box>
      ) : (
        <Box sx={{ border: "1px solid black", p: 2 }}>
          {query.data?.map((item) => {
            return (
              <Box key={item.name}>
                <img
                  src={`data:image/jpeg;base64, ${item.thumbnail}`}
                  alt="hm"
                ></img>
                <Box>{item.name}</Box>
              </Box>
            );
          })}
        </Box>
      )}
    </Container>
  );
};
