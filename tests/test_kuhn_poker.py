import jax
import jax.numpy as jnp
from pgx.kuhn_poker import KuhnPoker, CALL, BET, FOLD, CHECK

env = KuhnPoker()
init = jax.jit(env.init)
step = jax.jit(env.step)
observe = jax.jit(env.observe)


def test_init():
    key = jax.random.PRNGKey(0)
    state = init(key=key)
    assert state._cards[0] != state._cards[1]
    assert (state.legal_action_mask == jnp.bool_([0, 1, 0, 1])).all()


def test_step():
    key = jax.random.PRNGKey(0)
    # cards = [2, 0]
    state = init(key)
    state = step(state, CHECK)
    assert not state.terminated
    state = step(state, CHECK)
    assert state.terminated
    assert (state.rewards == jnp.float32([1, -1])).all()

    state = init(key)
    state = step(state, CHECK)
    assert not state.terminated
    state = step(state, BET)
    assert not state.terminated
    state = step(state, FOLD)
    assert state.terminated
    assert (state.rewards == jnp.float32([-1, 1])).all()

    state = init(key)
    state = step(state, CHECK)
    assert not state.terminated
    state = step(state, BET)
    assert not state.terminated
    state = step(state, CALL)
    assert state.terminated
    assert (state.rewards == jnp.float32([2, -2])).all()

    state = init(key)
    state = step(state, BET)
    assert not state.terminated
    state = step(state, FOLD)
    assert state.terminated
    assert (state.rewards == jnp.float32([1, -1])).all()

    state = init(key)
    state = step(state, BET)
    assert not state.terminated
    state = step(state, CALL)
    assert state.terminated
    assert (state.rewards == jnp.float32([2, -2])).all()


def test_legal_action():
    key = jax.random.PRNGKey(0)
    # cards = [2, 0]
    state = init(key)
    state = step(state, CHECK)
    assert (state.legal_action_mask == jnp.bool_([0, 1, 0, 1])).all()
    state = step(state, CHECK)
    assert state.terminated

    state = init(key)
    state = step(state, CHECK)
    assert (state.legal_action_mask == jnp.bool_([0, 1, 0, 1])).all()
    state = step(state, BET)
    assert (state.legal_action_mask == jnp.bool_([1, 0, 1, 0])).all()
    state = step(state, FOLD)
    assert state.terminated

    state = init(key)
    state = step(state, CHECK)
    assert (state.legal_action_mask == jnp.bool_([0, 1, 0, 1])).all()
    state = step(state, BET)
    assert (state.legal_action_mask == jnp.bool_([1, 0, 1, 0])).all()
    state = step(state, CALL)
    assert state.terminated

    state = init(key)
    state = step(state, BET)
    assert (state.legal_action_mask == jnp.bool_([1, 0, 1, 0])).all()
    state = step(state, FOLD)
    assert state.terminated

    state = init(key)
    state = step(state, BET)
    assert (state.legal_action_mask == jnp.bool_([1, 0, 1, 0])).all()
    state = step(state, CALL)
    assert state.terminated


def test_observation():
    key = jax.random.PRNGKey(0)
    state = init(key)
    """
    Player 0: K
    Player 1: J
    """
    state = step(state, BET)  # Player 0 bets 1 chip
    obs = observe(state, 0)
    assert (obs == jnp.bool_([0, 0, 1, 0, 1, 1, 0])).all()

    obs = observe(state, 1)
    assert (obs == jnp.bool_([1, 0, 0, 1, 0, 0, 1])).all()


def test_random_play():
    N = 100
    key = jax.random.PRNGKey(0)
    for _ in range(N):
        done = jnp.bool_(False)
        key, sub_key = jax.random.split(key)
        state = init(sub_key)
        while not done:
            legal_actions = jnp.where(state.legal_action_mask)[0]
            key, sub_key = jax.random.split(key)
            action = jax.random.choice(sub_key, legal_actions)
            state = step(state, action)
            done = state.terminated


def test_api():
    import pgx

    env = pgx.make("kuhn_poker")
    pgx.v1_api_test(env, 10)
