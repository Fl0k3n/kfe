import EditIcon from "@mui/icons-material/Edit";
import FolderIcon from "@mui/icons-material/Folder";
import { useEffect, useState } from "react";
import { getApis } from "./api/initializeApis";
import { Help } from "./components/Help";
import "./index.css";
import { FileViewer } from "./pages/FileViewer/FileViewer";
import { MetadataEditor } from "./pages/MetadataEditor/MetadataEditor";

type View = "viewer" | "metadata-editor";

function App() {
  const [view, setView] = useState<View>("viewer");
  const [startFileId, setStartFileId] = useState<number | undefined>(undefined);

  useEffect(() => {
    getApis().eventsApi.onUiOpenedOrRefreshedEventsOpenedOrRefreshedPost();
  }, []);

  const ViewIcon = view === "viewer" ? EditIcon : FolderIcon;

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
      <ViewIcon
        className="menuIcon"
        onClick={() => {
          setView((view) => (view === "viewer" ? "metadata-editor" : "viewer"));
        }}
        sx={{
          position: "fixed",
          bottom: "20px",
          left: "20px",
        }}
      ></ViewIcon>
      <Help />
    </div>
  );
}

export default App;
