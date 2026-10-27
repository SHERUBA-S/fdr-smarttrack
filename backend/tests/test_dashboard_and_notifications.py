def test_dashboard_metrics(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/api/v1/dashboards/metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_fdrs"] > 0
    assert float(data["total_recorded_principal"]) > 0
    assert len(data["status_distribution"]) > 0
    assert len(data["bank_distribution"]) > 0
    assert "disclaimer" in data

def test_notifications_lifecycle(client, institution_token):
    headers = {"Authorization": f"Bearer {institution_token}"}
    
    # 1. Fetch user notifications
    res = client.get("/api/v1/notifications/", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "unread_count" in data

    # 2. Mark all as read
    res_read_all = client.put("/api/v1/notifications/read-all", headers=headers)
    assert res_read_all.status_code == 200

    # 3. Check that unread count is 0
    res_after = client.get("/api/v1/notifications/", headers=headers)
    assert res_after.json()["unread_count"] == 0
