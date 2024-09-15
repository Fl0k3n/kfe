import { Box } from "@mui/material";
import { useState } from "react";
import { FileViewer } from "./pages/FileViewer/FileViewer";
import { MetadataEditor } from "./pages/MetadataEditor/MetadataEditor";

type View = "viewer" | "metadata-editor";

function App() {
  const [view, setView] = useState<View>("viewer");
  const [startFileId, setStartFileId] = useState<number | undefined>(undefined);
  return (
    <div>
      {view === "metadata-editor" && (
        <MetadataEditor startFileId={startFileId} />
      )}
      {view === "viewer" && (
        <FileViewer
          onNavigateToDescription={(x) => {
            setStartFileId(x);
            setView("metadata-editor");
          }}
        />
      )}
      <Box
        onClick={() => {
          setView((view) => (view === "viewer" ? "metadata-editor" : "viewer"));
        }}
        sx={{
          width: "50px",
          height: "50px",
          borderRadius: "50%",
          background: "#2046af",
          position: "fixed",
          bottom: "10px",
          left: "10px",
          cursor: "pointer",
        }}
      ></Box>
    </div>
  );
}

export default App;
