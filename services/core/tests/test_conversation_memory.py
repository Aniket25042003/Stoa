"""Tests for conversation-scoped long-term memory deletion."""

from unittest.mock import MagicMock, patch

from stoa_core.rag.conversation_memory import delete_conversation_memory


@patch("stoa_core.rag.conversation_memory.bump_kb_version")
@patch("stoa_core.rag.conversation_memory.get_supabase_admin")
def test_delete_conversation_memory_removes_matching_items(mock_sb, mock_bump) -> None:
    sb = MagicMock()
    mock_sb.return_value = sb
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[
            {"id": "item-1", "uri": "conversation:conv-1:checkpoint:6", "metadata": {}},
            {"id": "item-2", "uri": "conversation:conv-2:checkpoint:6", "metadata": {}},
            {"id": "item-3", "uri": None, "metadata": {"conversation_id": "conv-1"}},
            {"id": "item-4", "uri": "document:doc-1", "metadata": {"conversation_id": "conv-1"}},
        ]
    )

    deleted = delete_conversation_memory("org-1", "conv-1")

    assert deleted == 2
    assert sb.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.call_count == 2
    mock_bump.assert_called_once_with("org-1")


@patch("stoa_core.rag.conversation_memory.bump_kb_version")
@patch("stoa_core.rag.conversation_memory.get_supabase_admin")
def test_delete_conversation_memory_no_items(mock_sb, mock_bump) -> None:
    sb = MagicMock()
    mock_sb.return_value = sb
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )

    deleted = delete_conversation_memory("org-1", "conv-1")

    assert deleted == 0
    mock_bump.assert_not_called()
