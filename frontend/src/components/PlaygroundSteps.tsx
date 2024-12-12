import React, { useEffect, useState } from 'react';
import { Button, TextInput, ActionIcon, Box, Text, Paper, Group, Collapse, Badge, Transition, Loader } from '@mantine/core';
import { IconPlayerPlay, IconTrash, IconGripVertical, IconPlus, IconPlayerSkipForward, IconSquareRoundedX } from '@tabler/icons-react';
import type { Icon as TablerIconType } from '@tabler/icons-react';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { endWebagentSession, WebAgentRequestBody } from '@/services/webagentService';

export interface PlaygroundStep {
  id: string;
  action: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  isInitializing: boolean;
}

interface AnimatedIconProps {
  icon: TablerIconType;
  color: string;
  onClick: () => void;
  disabled?: boolean;
}

const AnimatedActionIcon = ({ icon: Icon, color, onClick, disabled = false, size = 18 }: AnimatedIconProps & { size?: number }) => {
  const [hovered, setHovered] = useState(false);

  return (
    <ActionIcon
      variant="subtle"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={onClick}
      disabled={disabled}
      className={`transition-all duration-200 ease-in-out ${hovered ? 'scale-110' : ''} ${disabled ? 'text-[var(--mantine-color-gray-5)]' : `text-[var(${color})]`
        } hover:bg-transparent disabled:bg-transparent`}
      size={size === 18 ? "sm" : "md"}
    >
      <Transition mounted={true} transition="scale" duration={200} timingFunction="ease">
        {(styles) => <Icon size={size} style={{ ...styles, stroke: hovered ? 'currentColor' : '1.5' }} />}
      </Transition>
    </ActionIcon>
  );
};

interface SortableStepProps {
  step: PlaygroundStep;
  index: number;
  updateStep: (id: string, field: keyof PlaygroundStep, value: string) => void;
  removeStep: (id: string) => void;
  runStep?: () => void;
  isAdditionalStep?: boolean;
  canRun: boolean;
}

const SortableStep = ({ step, index, updateStep, removeStep, runStep, isAdditionalStep, canRun }: SortableStepProps) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: step.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const getStatusColor = (status: PlaygroundStep['status']) => {
    switch (status) {
      case 'pending': return '--loggia-secondary';
      case 'running': return '--loggia-primary';
      case 'complete': return '--loggia-ready';
      case 'error': return '--mantine-color-red-6';
    }
  };

  return (
    <Paper
      ref={setNodeRef}
      style={style}
      shadow="sm"
      p="xs"
      withBorder
      className={`mb-2 bg-[var(--loggia-surface)] border-[var(${getStatusColor(step.status)})]`}
    >
      <Group justify="space-between" align="center" gap="xs" wrap="nowrap">
        <Group gap="xs" wrap="nowrap">
          <ActionIcon
            {...attributes}
            {...listeners}
            variant="subtle"
            className="cursor-move text-[var(--loggia-secondary)]"
          >
            <IconGripVertical size={16} />
          </ActionIcon>
          <Text fw={500} size="sm" className="text-[var(--loggia-text-primary)]">
            Step {index + 1}
          </Text>
          <Badge color={getStatusColor(step.status)} size="sm">
            {step.status}
          </Badge>
        </Group>
        <Group gap="xs" wrap="nowrap">
          {isAdditionalStep && runStep && (
            <AnimatedActionIcon
              icon={IconPlayerSkipForward}
              color="--loggia-primary"
              onClick={runStep}
              disabled={!canRun || step.status === 'complete' || step.status === 'running'}
              size={24}
            />
          )}
          <AnimatedActionIcon
            icon={IconTrash}
            color="--mantine-color-red-6"
            onClick={() => removeStep(step.id)}
            disabled={step.status !== 'pending'}
          />
        </Group>
      </Group>
      <TextInput
        value={step.action}
        onChange={(e) => updateStep(step.id, 'action', e.target.value)}
        placeholder="Enter action description"
        variant="filled"
        size="xs"
        mt={4}
        disabled={step.status !== 'pending'}
        classNames={{
          input: 'focus:border-[var(--loggia-border-active)]'
        }}
      />
    </Paper>
  );
};

interface PlaygroundStepsProps {
  onRunInitialTest: (testData: WebAgentRequestBody) => Promise<void>;
  onRunAdditionalTest: (action: string) => Promise<void>;
  initialSteps_: PlaygroundStep[];
  processId: string;
  onSessionEnd: () => void
}

const PlaygroundSteps: React.FC<PlaygroundStepsProps> = ({
  onRunInitialTest,
  onRunAdditionalTest,
  initialSteps_,
  processId,
  onSessionEnd
}) => {
  const [startingUrl, setStartingUrl] = useState('');
  const [goal, setGoal] = useState('');
  const [initialSteps, setInitialSteps] = useState<PlaygroundStep[]>([]);
  const [additionalSteps, setAdditionalSteps] = useState<PlaygroundStep[]>([]);
  const [initialRunOngoing, setInitialRunOngoing] = useState(false);
  const [initialRunCompleted, setInitialRunCompleted] = useState(false);
  const [currentAdditionalStep, setCurrentAdditionalStep] = useState(0);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

const addNewStep = (isAdditional: boolean) => {
  const newId = (isAdditional ? additionalSteps.length : initialSteps.length + 1).toString();
  const newStep: PlaygroundStep = {
    id: newId,
    action: '',
    status: 'pending' as const,
    isInitializing: false  // Add the missing property
  };

  if (isAdditional) {
    setAdditionalSteps([...additionalSteps, newStep]);
  } else {
    setInitialSteps([...initialSteps, newStep]);
  }
};

  const updateStep = (id: string, field: keyof PlaygroundStep, value: string, isAdditional: boolean) => {
    const updateStepsList = (steps: PlaygroundStep[]) =>
      steps.map(step => step.id === id ? { ...step, [field]: value } : step);

    if (isAdditional) {
      setAdditionalSteps(updateStepsList(additionalSteps));
    } else {
      setInitialSteps(updateStepsList(initialSteps));
    }
  };

  const removeStep = (id: string, isAdditional: boolean) => {
    if (isAdditional) {
      setAdditionalSteps(additionalSteps.filter(step => step.id !== id));
    } else {
      setInitialSteps(initialSteps.filter(step => step.id !== id));
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleDragEnd = (event: any, isAdditional: boolean) => {
    const { active, over } = event;
    if (active.id !== over.id) {
      const moveSteps = (items: PlaygroundStep[]) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      };

      if (isAdditional) {
        setAdditionalSteps(moveSteps(additionalSteps));
      } else {
        setInitialSteps(moveSteps(initialSteps));
      }
    }
  };

  useEffect(() => {
    if (initialSteps_.length > 0) {
      const lastIndex = initialSteps_.length - 1;

      setInitialSteps(initialSteps_.map((step, index) =>
        index === lastIndex ? { ...step, status: 'running' } : { ...step, status: 'complete' }
      ));
    }
  }, [initialSteps_])

    // needed and fixed
    const runInitialSteps = async () => {
      console.log('Running initial steps:', { startingUrl, goal, initialSteps });
      // Run even if there are no initial steps
      setInitialRunOngoing(true)

      const plan = initialSteps.length > 0
        ? initialSteps
            .map((step, index) => `(${index + 1}) step ${index + 1}: ${step.action}`)
            .join(', ')
        : ''; // Empty plan for no steps

      // Simulate brief delay
      await new Promise(resolve => setTimeout(resolve, 500));

      await onRunInitialTest({
        goal: goal,
        starting_url: startingUrl,
        plan: plan,
        session_id: ""
      });

      setInitialRunOngoing(false);
      setInitialRunCompleted(true);
    };

    // Update the runAdditionalStep function
    const runAdditionalStep = async (stepId: string) => {
      const stepIndex = additionalSteps.findIndex(step => step.id === stepId);
      if (stepIndex !== currentAdditionalStep) return;

      try {
        // Update step status to running
        setAdditionalSteps(steps => steps.map((step, index) =>
          index === stepIndex ? { ...step, status: 'running' } : step
        ));

        // Get the step action and call the API
        const step = additionalSteps[stepIndex];
        await onRunAdditionalTest(step.action);

        // Update step status to complete
        setAdditionalSteps(steps => steps.map((step, index) =>
          index === stepIndex ? { ...step, status: 'complete' } : step
        ));

        // Move to next step
        setCurrentAdditionalStep(current => current + 1);
      } catch (error) {
        // Handle error by setting step status to error
        setAdditionalSteps(steps => steps.map((step, index) =>
          index === stepIndex ? { ...step, status: 'error' } : step
        ));
        console.error('Failed to run additional step:', error);
      }
    };

  const endSession = () => {
    onSessionEnd()
    endWebagentSession(processId)
    setInitialRunCompleted(false);
    setStartingUrl('');
    setGoal('');
    setInitialSteps([]);
    setAdditionalSteps([]);
    setCurrentAdditionalStep(0);
  };

  return (
    <Box p={24} maw={600} mx="auto" className="bg-[var(--loggia-background)] rounded-lg shadow-md">
      <Text fw={700} size="xl" className="text-[var(--loggia-primary)]">Dynamic Step Form</Text>
      <TextInput
        label="Starting URL"
        value={startingUrl}
        onChange={(e) => setStartingUrl(e.target.value)}
        placeholder="Enter starting URL"
        required
        disabled={initialRunOngoing || initialRunCompleted}
      />
      <TextInput
        label="Goal"
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        placeholder="Enter goal"
        required
        disabled={initialRunOngoing || initialRunCompleted}
      />
      <Box>
        <Text fw={600} size="md" mb={8} className="text-[var(--loggia-text-primary)]">Initial Steps</Text>
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(e) => handleDragEnd(e, false)}>
          <SortableContext items={initialSteps} strategy={verticalListSortingStrategy}>
            {initialSteps.map((step, index) => (
              <SortableStep
                key={step.id}
                step={step}
                index={index}
                updateStep={(id, field, value) => updateStep(id, field, value, false)}
                removeStep={(id) => removeStep(id, false)}
                canRun={false}
              />
            ))}
          </SortableContext>
        </DndContext>
        <Group justify="space-between" mt={16}>
          <Button
            onClick={() => addNewStep(false)}
            variant="outline"
            size="sm"
            leftSection={<IconPlus size={14} />}
            className="border-[var(--loggia-primary)] text-[var(--loggia-primary)] hover:bg-[var(--loggia-primary-light)]"
            disabled={initialRunOngoing || initialRunCompleted}
          >
            Add initial step
          </Button>
          {!initialRunCompleted && (
            <Button
              onClick={runInitialSteps}
              size="sm"
              className="bg-[var(--loggia-primary)] text-white hover:bg-[var(--loggia-primary-hover)] disabled:bg-[var(--loggia-secondary)]"
              disabled={initialRunOngoing}
              leftSection={initialRunOngoing ? <Loader color="white" size="sm" /> : <IconPlayerPlay size={16} />}
            >
              {initialRunOngoing ? 'Running...' : 'Run Initial Steps'}
            </Button>
          )}
        </Group>
      </Box>

      <Collapse in={initialRunCompleted}>
        <Box mt={24}>
          <Text fw={600} size="md" mb={8} className="text-[var(--loggia-text-primary)]">Additional Steps</Text>
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(e) => handleDragEnd(e, true)}>
            <SortableContext items={additionalSteps} strategy={verticalListSortingStrategy}>
              {additionalSteps.map((step, index) => (
                <SortableStep
                  key={step.id}
                  step={step}
                  index={index}
                  updateStep={(id, field, value) => updateStep(id, field, value, true)}
                  removeStep={(id) => removeStep(id, true)}
                  runStep={() => runAdditionalStep(step.id)}
                  isAdditionalStep
                  canRun={index === currentAdditionalStep}
                />
              ))}
            </SortableContext>
          </DndContext>
          <Button
            onClick={() => addNewStep(true)}
            variant="outline"
            size="sm"
            leftSection={<IconPlus size={14} />}
            className="border-[var(--loggia-primary)] text-[var(--loggia-primary)] hover:bg-[var(--loggia-primary-light)] mt-4"
          >
            Add additional step
          </Button>
        </Box>
      </Collapse>

      {initialRunCompleted && (
        <Button
          onClick={endSession}
          leftSection={<IconSquareRoundedX size={16} />}
          size="sm"
          className="bg-[var(--mantine-color-red-6)] text-white hover:bg-[var(--mantine-color-red-7)] mt-8"
        >
          End Session
        </Button>
      )}
    </Box>
  );
};

export default PlaygroundSteps;