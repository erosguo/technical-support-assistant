import pytest

from app.services.notification import (
    NotificationProvider,
    notify_escalation,
    send_notification,
)


class TestNotification:
    def test_send_notification_feishu(self):
        result = send_notification(
            provider=NotificationProvider.FEISHU,
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/x",
            title="工单升级",
            content="生产环境故障需要人工介入",
        )
        assert result["success"] is True
        assert result["provider"] == "FEISHU"
        assert result["sent_at"]
        assert result["payload"] == {
            "msg_type": "text",
            "content": {"text": "工单升级\n生产环境故障需要人工介入"},
        }

    def test_send_notification_dingtalk(self):
        result = send_notification(
            provider=NotificationProvider.DINGTALK,
            webhook_url="https://oapi.dingtalk.com/robot/send?token=x",
            title="告警通知",
            content="数据库连接超时",
        )
        assert result["success"] is True
        assert result["provider"] == "DINGTALK"
        assert result["payload"] == {
            "msgtype": "text",
            "text": {"content": "告警通知\n数据库连接超时"},
        }

    def test_send_notification_slack(self):
        result = send_notification(
            provider=NotificationProvider.SLACK,
            webhook_url="https://hooks.slack.com/services/x",
            title="Incident Escalation",
            content="Production service is down",
        )
        assert result["success"] is True
        assert result["provider"] == "SLACK"
        assert result["payload"] == {
            "text": "Incident Escalation\nProduction service is down"
        }

    def test_send_notification_unknown_provider(self):
        with pytest.raises(ValueError):
            send_notification(
                provider="UNKNOWN_IM",
                webhook_url="https://example.com/hook",
                title="t",
                content="c",
            )

    def test_notify_escalation(self):
        result = notify_escalation(
            provider=NotificationProvider.FEISHU,
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/x",
            ticket_title="严重故障升级",
            ticket_description="订单服务不可用，请立即处理",
        )
        assert result["success"] is True
        assert result["provider"] == "FEISHU"
        assert result["payload"] == {
            "msg_type": "text",
            "content": {"text": "严重故障升级\n订单服务不可用，请立即处理"},
        }
