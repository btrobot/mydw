import { Button, Form, Input, Modal, Space, Typography } from 'antd';
import { useCallback, useEffect, useRef, useState } from 'react';

import {
  AdminApiError,
  mapStepUpVerifyError,
  type AdminStepUpScope,
  verifyAdminStepUpPassword,
} from './auth-client.js';

type StepUpPromptOptions = {
  scope: AdminStepUpScope;
  actionLabel: string;
  description: string;
};

type StepUpPromptState = StepUpPromptOptions & {
  open: boolean;
};

type PendingRequest = {
  resolve: (token: string) => void;
  reject: (error: Error) => void;
};

export class AdminStepUpCancelledError extends Error {
  constructor(message = 'Admin step-up cancelled') {
    super(message);
  }
}

export function isAdminStepUpCancelledError(error: unknown): error is AdminStepUpCancelledError {
  return error instanceof AdminStepUpCancelledError;
}

export function useAdminStepUp(options: {
  accessToken: string | null;
  onExpiredSession: () => void;
}): {
  requestStepUp: (prompt: StepUpPromptOptions) => Promise<string>;
  stepUpModal: JSX.Element;
} {
  const { accessToken, onExpiredSession } = options;
  const [form] = Form.useForm<{ password: string }>();
  const [promptState, setPromptState] = useState<StepUpPromptState | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const pendingRequestRef = useRef<PendingRequest | null>(null);

  const closePrompt = useCallback((error?: Error) => {
    form.resetFields();
    setSubmitting(false);
    setErrorMessage(null);
    setPromptState(null);
    const pendingRequest = pendingRequestRef.current;
    pendingRequestRef.current = null;
    if (error && pendingRequest) {
      pendingRequest.reject(error);
    }
  }, [form]);

  useEffect(() => {
    return () => {
      if (pendingRequestRef.current) {
        pendingRequestRef.current.reject(new AdminStepUpCancelledError('Admin step-up closed before completion'));
        pendingRequestRef.current = null;
      }
    };
  }, []);

  const requestStepUp = useCallback(
    (prompt: StepUpPromptOptions) =>
      new Promise<string>((resolve, reject) => {
        pendingRequestRef.current = { resolve, reject };
        form.resetFields();
        setSubmitting(false);
        setErrorMessage(null);
        setPromptState({ ...prompt, open: true });
      }),
    [form]
  );

  async function handleSubmit(values: { password: string }): Promise<void> {
    if (!accessToken || !promptState || !pendingRequestRef.current) {
      closePrompt(new AdminStepUpCancelledError('Admin step-up unavailable'));
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await verifyAdminStepUpPassword(accessToken, values.password, promptState.scope);
      const pendingRequest = pendingRequestRef.current;
      pendingRequestRef.current = null;
      form.resetFields();
      setSubmitting(false);
      setErrorMessage(null);
      setPromptState(null);
      pendingRequest?.resolve(response.step_up_token);
    } catch (error) {
      setSubmitting(false);
      if (error instanceof AdminApiError && error.errorCode === 'token_expired') {
        onExpiredSession();
        closePrompt(new AdminStepUpCancelledError('Admin session expired during step-up'));
        return;
      }
      setErrorMessage(error instanceof AdminApiError ? mapStepUpVerifyError(error.errorCode) : mapStepUpVerifyError());
    }
  }

  return {
    requestStepUp,
    stepUpModal: (
      <Modal
        open={Boolean(promptState?.open)}
        title={promptState ? `Confirm password: ${promptState.actionLabel}` : 'Confirm password'}
        onCancel={() => closePrompt(new AdminStepUpCancelledError())}
        destroyOnHidden
        footer={null}
        maskClosable={!submitting}
        closable={!submitting}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {promptState?.description ??
              'Before continuing, confirm your admin password. A short-lived step-up token will be used for this action only.'}
          </Typography.Paragraph>

          {errorMessage ? <Typography.Text type="danger">{errorMessage}</Typography.Text> : null}

          <Form<{ password: string }> form={form} layout="vertical" onFinish={(values) => void handleSubmit(values)}>
            <Form.Item
              label="Password"
              name="password"
              rules={[{ required: true, message: 'Please confirm your admin password.' }]}
            >
              <Input.Password autoComplete="current-password" placeholder="Enter your password" />
            </Form.Item>

            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => closePrompt(new AdminStepUpCancelledError())} disabled={submitting}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit" loading={submitting}>
                Confirm and continue
              </Button>
            </Space>
          </Form>
        </Space>
      </Modal>
    ),
  };
}
