from insurance_data_layer.adapters.base import ADAPTERS, SourceAdapter
from insurance_data_layer.adapters.hansemerkur import HanseMerkurAdapter
from insurance_data_layer.adapters.santevet import SantevetAdapter

__all__ = ["ADAPTERS", "HanseMerkurAdapter", "SantevetAdapter", "SourceAdapter"]
