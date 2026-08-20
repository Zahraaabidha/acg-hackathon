import { useOutletContext } from "react-router-dom";
import { KnowledgeGraph } from "../../components/KnowledgeGraph";

export default function GraphPage() {
  const { data } = useOutletContext();

  return (
    <div className="space-y-6 pb-16">
      <KnowledgeGraph graph={data.knowledgeGraph} />
    </div>
  );
}
