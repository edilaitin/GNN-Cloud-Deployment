import json
import dgl
import torch
from Wrapper_Z3 import Wrapper_Z3
from gnn.dgl_graph import DGLGraph
from gnn.main import get_graph_data, to_assignment_matrix, count_matches_and_diffs


class Wrapper_GNN:
    def __init__(self, model_path="trained_model_SecureWeb_DO.pth"):
        # load pre-existing trained model
        self.model = torch.load(model_path)
        # set the model to evaluation mode
        self.model.eval()

    def solve(self, application_model_json, offers_json):
        # Obtain data in required form (ignore solution)
        app_json = Wrapper_Z3().solve(application_model_json, offers_json, out=False)
        # Transform into graph data structure
        graph = get_graph_data(app_json, app_json["application"])
        # Transform into required DGL graph structure
        dataset = DGLGraph(graph)
        dgl_graph = dataset[0].to('cuda')

        # create empty lists to store the predictions and true labels
        y_pred = []
        y_true = []

        dec_graph = dgl_graph['component', :, 'vm']
        print(dec_graph)

        edge_label = dec_graph.edata[dgl.ETYPE]
        comp_feats = dgl_graph.nodes['component'].data['feat']
        vm_feats = dgl_graph.nodes['vm'].data['feat']
        node_features = {'component': comp_feats, 'vm': vm_feats}
        with torch.no_grad():
            logits = self.model(dgl_graph, node_features, dec_graph)
        pred = logits.argmax(dim=-1)
        y_pred.append(pred)
        assignment_pred = to_assignment_matrix(dgl_graph, dec_graph, pred, 5)
        assignment_actual = to_assignment_matrix(dgl_graph, dec_graph, edge_label, 5)
        matches, diffs = count_matches_and_diffs([element for row in assignment_pred for element in row],
                                                 [element for row in assignment_actual for element in row])
        print(f"{matches} values match; {diffs} don't")
        print(f"Prediction {assignment_pred}")
        print(f"Actual {assignment_actual}")
        return assignment_pred

