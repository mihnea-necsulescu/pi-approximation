<script lang="ts">
    import {fetchEventSource} from "@microsoft/fetch-event-source";

    type Point = [number, number]

    let numPoints: number = 10000;
    let isRunning: boolean = false;
    let coordinates: Point[] = [];
    let pointsInside: number = 0;
    let piApproximation: number = 0;
    let progress: number = 0;
    let totalPoints: number = 0;
    let pointsReceived: number = 0;
    let abortController: AbortController | null = null;

    function isPointInsideCircle(x: number, y: number): boolean {
        return (x * x + y * y) <= 1;
    }

    function calculatePi(): void {
        if (pointsReceived > 0) {
            piApproximation = 4 * (pointsInside / pointsReceived);
        }
    }

    async function startSimulation(): Promise<void> {
        if (isRunning) return;

        coordinates = [];
        progress = 0;
        pointsReceived = 0;
        isRunning = true;
        abortController = new AbortController();

        try {
            await fetchEventSource('http://localhost:8000/generatePoints', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream'
                },
                body: JSON.stringify({num_points: numPoints}),
                signal: abortController.signal,

                async onopen(response) {
                    if (response.ok) {
                        console.log('SSE connection opened');
                    } else {
                        throw new Error(`HTTP error status: ${response.status}`);
                    }
                },

                onmessage(event) {
                    handleSSEEvent(event.event || 'message', event.data);
                },

                onerror(error) {
                    console.error('SSE error:', error);
                    throw error;
                },

                onclose() {
                    console.log('SSE connection closed');
                    isRunning = false;
                }
            });
        } catch (error) {
            console.error('Error:', error);
        } finally {
            isRunning = false;
            abortController = null;
        }
    }

    function handleSSEEvent(eventType: string, data: string): void {
        try {
            const parsedData = JSON.parse(data);

            switch (eventType) {
                case 'start':
                    totalPoints = parsedData.total_points;
                    pointsInside = 0;
                    piApproximation = 0;
                    break;

                case 'batch':
                    coordinates = [...coordinates, ...parsedData.points];

                    const newPointsInsideCircle = parsedData.points.filter(([x, y]: Point) => isPointInsideCircle(x, y)).length;
                    pointsInside += newPointsInsideCircle;

                    pointsReceived = parsedData.points_sent;

                    progress = totalPoints > 0 ? (pointsReceived / totalPoints) * 100 : 0;

                    calculatePi();
                    break;

                case 'end':
                    isRunning = false;
                    break;
            }
        } catch (error) {
            console.error('Error parsing SSE data:', error);
        }
    }

    function stopSimulation(): void {
        if (abortController) {
            abortController.abort();
            abortController = null;
        }
        isRunning = false;
    }

</script>

<main>
    <h1>Pi Approximation</h1>

    <div class="controls">
        <label for="num-points">Please enter N:</label>
        <input
                id="num-points"
                type="number"
                bind:value={numPoints}
                disabled={isRunning}
        />

        <button on:click={startSimulation} disabled={isRunning}>
            {isRunning ? 'Running...' : 'Start Simulation'}
        </button>

        {#if isRunning}
            <button on:click={stopSimulation}>Stop</button>
        {/if}
    </div>

    {#if pointsReceived > 0}
        <div>
            <h2>π ≈ {piApproximation.toFixed(10)}</h2>
        </div>
    {/if}

    {#if totalPoints > 0}
        <div>
            <h3>Progress: {pointsReceived}/{totalPoints} ({progress.toFixed(1)}%)</h3>
        </div>
    {/if}
</main>