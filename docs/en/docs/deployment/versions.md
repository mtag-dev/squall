# About Squall versions

**Squall** is already being used in production in many applications and systems. And the test coverage is kept at 100%. But its development is still moving quickly.

New features are added frequently, bugs are fixed regularly, and the code is still continuously improving.

That's why the current versions are still `0.x.x`, this reflects that each version could potentially have breaking changes. This follows the <a href="https://semver.org/" class="external-link" target="_blank">Semantic Versioning</a> conventions.

You can create production applications with **Squall** right now (and you have probably been doing it for some time), you just have to make sure that you use a version that works correctly with the rest of your code.

## Pin your `squall` version


## Available versions

You can see the available versions (e.g. to check what is the current latest) in the [Release Notes](../release-notes.md){.internal-link target=_blank}.

## About versions

## Upgrading the Squall versions

You should add tests for your app.

With **Squall** it's very easy (thanks to Starlette), check the docs: [Testing](../tutorial/testing.md){.internal-link target=_blank}

After you have tests, then you can upgrade the **Squall** version to a more recent one, and make sure that all your code is working correctly by running your tests.

If everything is working, or after you make the necessary changes, and all your tests are passing, then you can pin your `squall` to that new recent version.

## About Starlette

You shouldn't pin the version of `starlette`.

Different versions of **Squall** will use a specific newer version of Starlette.

So, you can just let **Squall** use the correct Starlette version.

## About Pydantic

Pydantic includes the tests for **Squall** with its own tests, so new versions of Pydantic (above `1.0.0`) are always compatible with Squall.

You can pin Pydantic to any version above `1.0.0` that works for you and below `2.0.0`.

For example:

```txt
pydantic>=1.2.0,<2.0.0
```
