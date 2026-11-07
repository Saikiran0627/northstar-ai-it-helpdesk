from __future__ import annotations

from northstar_helpdesk.knowledge_base import KnowledgeBase


def test_vpn_query_retrieves_vpn_doc(test_settings):
    kb = KnowledgeBase(test_settings.knowledge_dir)

    results = kb.search("VPN keeps disconnecting before a client presentation")

    assert results
    assert results[0].doc_id == "vpn-remote-access"
    assert results[0].score > 0
